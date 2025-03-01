# Building SLiCAP Documentation

## Creating A workflow

Workflows are created after the keyword "on". In this yaml file I create two possible workflows. 

1. One workflow is triggered when a "push" is made to the main branch of this repository.

2. The second workflow is triggered when publising and uploads a distribution package to pypi

### SLiCAP Triggered Workflow

This workflow is triggered from the SLiCAP_python repository. When a 'Push' is made in the SLiCAP_python repository a [Repository Webhook](https://docs.github.com/en/free-pro-team@latest/rest/repos/webhooks?apiVersion=2022-11-28#create-a-repository-webhook) request is made with the tag "Trigger_Workflow" and sent to this repository.

## Jobs

The jobs that need to be completed are

1. Checkout the SLiCAP repository

2. Install Required SLiCAP Dependencies

3. Install SLiCAP

4. Build the SLiCAP documentation

5. Setup pages

6. upload artifact

# Building pypi distribution package

The main strategy is from the [tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/), but SLiCAP uses setuptools so I also use this [tutorial](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/). This workflow is only triggered when publishing.

1. Install Twine to upload to pypi

2. Update and Install build

3. Checkout the SLiCAP repository

4. Build a source distribution

5. Build a distribution wheel

6. Upload to pypi using twine

