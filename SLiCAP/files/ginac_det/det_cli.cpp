// slicap_det — C++/GiNaC copy of SLiCAP.SLiCAPmath.det() for methods "ME"
// and "BS" only, including the numeric pre-elimination (_eliminateVars) and
// the float2rational analog. Benchmark experiment per SLiCAP_GiNAC.md; the
// Python det() remains the executable specification.
//
// Input (stdin or file argument): line 1 = dimension n, then n*n entries,
// row-major, one expression per line, sympy str() syntax with '**' already
// converted to '^' by the exporting harness.
//
// Output: the determinant on stdout (GiNaC default syntax, '^' powers);
// timing JSON on stderr: {"dim":..,"method":..,"reduce":..,
//                         "parse_s":..,"compute_s":..,"print_s":..}

#include <ginac/ginac.h>
#include <ginac/version.h>
#include <cln/real.h>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace GiNaC;

// --------------------------------------------------------------------------
// helpers

// sympy's e.is_number == "contains no free symbols" (2*pi IS a number:
// GiNaC's Pi is a constant, not a symbol, so this matches).
static bool has_symbol(const ex &e)
{
    if (is_a<symbol>(e))
        return true;
    for (size_t i = 0; i < e.nops(); ++i)
        if (has_symbol(e.op(i)))
            return true;
    return false;
}

static bool matrix_has_symbol(const matrix &M)
{
    for (unsigned i = 0; i < M.rows(); ++i)
        for (unsigned j = 0; j < M.cols(); ++j)
            if (has_symbol(M(i, j)))
                return true;
    return false;
}

static bool is_zero_matrix(const matrix &M)
{
    for (unsigned i = 0; i < M.rows(); ++i)
        for (unsigned j = 0; j < M.cols(); ++j)
            if (!M(i, j).is_zero())
                return false;
    return true;
}

// float2rational analog: replace every real float by its exact rational
// value (CLN rationalize). The harness already rationalizes on export;
// this is a defensive second layer so float arithmetic can never occur.
struct rationalize_map : public map_function {
    ex operator()(const ex &e) override
    {
        if (is_a<numeric>(e)) {
            const numeric &n = ex_to<numeric>(e);
            if (n.is_real() && !n.is_rational())
                return numeric(cln::cl_N(cln::rationalize(cln::realpart(n.to_cl_N()))));
            return e;
        }
        return e.map(*this);
    }
};

// sympy Matrix.minor_submatrix(r, c)
static matrix minor_submatrix(const matrix &M, unsigned r, unsigned c)
{
    const unsigned rows = M.rows() - 1;
    const unsigned cols = M.cols() - 1;
    matrix m(rows, cols);
    for (unsigned i = 0, mi = 0; i < M.rows(); ++i) {
        if (i == r)
            continue;
        for (unsigned j = 0, mj = 0; j < M.cols(); ++j) {
            if (j == c)
                continue;
            m(mi, mj) = M(i, j);
            ++mj;
        }
        ++mi;
    }
    return m;
}

// --------------------------------------------------------------------------
// SLiCAPmath._find_numeric_entry
static bool find_numeric_entry(const matrix &M, unsigned &k, unsigned &l)
{
    const unsigned dim = M.rows();
    for (unsigned i = 0; i < dim; ++i)
        for (unsigned j = 0; j < dim; ++j)
            if (!M(i, j).is_zero() && !has_symbol(M(i, j))) {
                k = i;
                l = j;
                return true;
            }
    return false;
}

// SLiCAPmath._eliminateVars
static matrix eliminate_vars(matrix M, ex &factor)
{
    factor = 1;
    unsigned dim = M.rows();
    unsigned k = 0, l = 0;
    bool found = find_numeric_entry(M, k, l);
    while (found && dim > 1) {
        factor *= M(k, l);
        if ((k + l) % 2)
            factor = -factor;
        for (unsigned i = 0; i < dim; ++i) {
            if (!M(i, l).is_zero() && i != k) {
                for (unsigned j = 0; j < dim; ++j) {
                    if (!M(k, j).is_zero() && j != l)
                        M(i, j) = (M(i, j) - M(i, l) * M(k, j) / M(k, l)).expand();
                }
            }
        }
        M = minor_submatrix(M, k, l);
        --dim;
        found = find_numeric_entry(M, k, l);
    }
    return M;
}

// SLiCAPmath._detME
static ex det_ME(const matrix &M)
{
    const unsigned dim = M.rows();
    ex D = 0;
    if (dim == 2) {
        D = M(0, 0) * M(1, 1) - M(1, 0) * M(0, 1);
    } else {
        for (unsigned row = 0; row < dim; ++row) {
            if (!M(row, 0).is_zero()) {
                ex minor = det_ME(minor_submatrix(M, row, 0));
                if (!minor.is_zero()) {
                    if (row % 2)
                        D -= M(row, 0) * minor;
                    else
                        D += M(row, 0) * minor;
                }
            }
        }
    }
    return D.expand();
}

// SLiCAPmath._detBS
// Faithful copy including the pivot-search range(k+1, dim-1), which never
// inspects the LAST row (and whose "singular" early return is unreachable)
// — flagged to Anton 2026-07-13, kept verbatim for comparability.
// sympy's sp.factor(a/b) on the exact Bareiss division is rendered as exact
// polynomial division with a normal() fallback (entries may hold 1/R terms).
static ex det_BS(const matrix &Min)
{
    matrix newM = Min;
    int sign = 1;
    const unsigned dim = newM.rows();
    for (unsigned k = 0; k + 1 < dim; ++k) {
        if (newM(k, k).is_zero()) {
            for (unsigned m = k + 1; m + 1 < dim; ++m) {
                if (!newM(m, k).is_zero()) {
                    for (unsigned j = 0; j < dim; ++j) {
                        ex tmp = newM(m, j);
                        newM(m, j) = newM(k, j);
                        newM(k, j) = tmp;
                    }
                    sign = -sign;
                    break;
                }
            }
        }
        for (unsigned i = k + 1; i < dim; ++i) {
            for (unsigned j = k + 1; j < dim; ++j) {
                ex e = newM(k, k) * newM(i, j) - newM(i, k) * newM(k, j);
                if (k) {
                    // divide() throws if entries hold negative powers (1/R
                    // terms in MNA matrices) — normal() is the exact fallback.
                    try {
                        ex q;
                        if (divide(e.expand(), newM(k - 1, k - 1), q))
                            newM(i, j) = q;
                        else
                            newM(i, j) = normal(e / newM(k - 1, k - 1));
                    } catch (std::exception &) {
                        newM(i, j) = normal(e / newM(k - 1, k - 1));
                    }
                } else {
                    newM(i, j) = e;
                }
            }
            newM(i, k) = 0;
        }
    }
    ex D = sign * newM(dim - 1, dim - 1);
    return normal(D);
}

// SLiCAPmath.det() for methods ME | BS
static ex slicap_det(matrix M, const std::string &method, bool reduce)
{
    rationalize_map to_rational;
    for (unsigned i = 0; i < M.rows(); ++i)
        for (unsigned j = 0; j < M.cols(); ++j)
            M(i, j) = to_rational(M(i, j));

    ex factor = 1;
    if (reduce && matrix_has_symbol(M))
        M = eliminate_vars(M, factor);

    const unsigned dim = M.rows();
    if (is_zero_matrix(M))
        return 0;
    if (dim == 1)
        return M(0, 0) * factor;
    if (dim == 2)
        return (M(0, 0) * M(1, 1) - M(1, 0) * M(0, 1)).expand() * factor;
    if (method == "ME")
        return det_ME(M) * factor;
    if (method == "BS")
        return det_BS(M) * factor;
    throw std::runtime_error("Unknown method: " + method + " (use ME or BS)");
}

// --------------------------------------------------------------------------

int main(int argc, char *argv[])
{
    std::string method = "ME";
    bool reduce = true;   // ini.reduce_matrix default
    std::string infile;

    for (int a = 1; a < argc; ++a) {
        std::string arg = argv[a];
        if (arg == "--method" && a + 1 < argc)
            method = argv[++a];
        else if (arg == "--no-reduce")
            reduce = false;
        else if (arg == "--version") {
            // protocol number first: the Python side checks it
            std::cout << "slicap_det protocol 1 (GiNaC "
                      << GINACLIB_MAJOR_VERSION << "."
                      << GINACLIB_MINOR_VERSION << "."
                      << GINACLIB_MICRO_VERSION << ")\n";
            return 0;
        } else if (arg == "--help" || arg == "-h") {
            std::cout << "usage: slicap_det [--method ME|BS] [--no-reduce] [file]\n"
                         "input: line 1 = n, then n*n entries one per line ('^' powers)\n";
            return 0;
        } else
            infile = arg;
    }

    std::istream *in = &std::cin;
    std::ifstream f;
    if (!infile.empty()) {
        f.open(infile);
        if (!f) {
            std::cerr << "cannot open " << infile << std::endl;
            return 1;
        }
        in = &f;
    }

    using clock = std::chrono::steady_clock;
    auto secs = [](clock::time_point a, clock::time_point b) {
        return std::chrono::duration<double>(b - a).count();
    };

    // ---- parse ----
    auto t0 = clock::now();
    std::string line;
    unsigned n = 0;
    while (std::getline(*in, line)) {
        if (line.find_first_not_of(" \t\r") == std::string::npos)
            continue;
        n = std::stoul(line);
        break;
    }
    if (n == 0) {
        std::cerr << "no dimension line" << std::endl;
        return 1;
    }

    symtab table;
    table["pi"] = Pi;
    table["I"] = I;
    table["E"] = exp(1);
    parser reader(table);   // non-strict: unknown names become symbols

    matrix M(n, n);
    unsigned count = 0;
    while (count < n * n && std::getline(*in, line)) {
        if (line.find_first_not_of(" \t\r") == std::string::npos)
            continue;
        try {
            M(count / n, count % n) = reader(line);
        } catch (std::exception &e) {
            std::cerr << "parse error at entry " << count << ": " << e.what()
                      << "\n  " << line << std::endl;
            return 1;
        }
        ++count;
    }
    if (count != n * n) {
        std::cerr << "expected " << n * n << " entries, got " << count << std::endl;
        return 1;
    }
    auto t1 = clock::now();

    // ---- compute ----
    ex D;
    try {
        D = slicap_det(M, method, reduce);
    } catch (std::exception &e) {
        std::cerr << "compute error: " << e.what() << std::endl;
        return 1;
    }
    auto t2 = clock::now();

    // ---- print ----
    std::ostringstream out;
    out << D;
    std::cout << out.str() << std::endl;
    auto t3 = clock::now();

    std::cerr << "{\"dim\": " << n
              << ", \"method\": \"" << method << "\""
              << ", \"reduce\": " << (reduce ? "true" : "false")
              << ", \"parse_s\": " << secs(t0, t1)
              << ", \"compute_s\": " << secs(t1, t2)
              << ", \"print_s\": " << secs(t2, t3)
              << "}" << std::endl;
    return 0;
}
