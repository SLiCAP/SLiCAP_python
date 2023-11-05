# Building SLiCAP Documentation

## Creating A workflow

Workflows are created after the keyword "on". In this yaml file I create two possible workflows. 

1. One workflow is triggered when a "push" is made to the main branch of this repository.

2. The second workflow is triggered from another repository. 

### SLiCAP Triggered Workflow

This workflow is triggered from the SLiCAP_python repository. When a 'Push' is made in the SLiCAP_python repository a [Repository Webhook](https://docs.github.com/en/free-pro-team@latest/rest/repos/webhooks?apiVersion=2022-11-28#create-a-repository-webhook) request is made with the tag "Trigger_Workflow" and sent to this repository.

## Jobs

The jobs that need to be completed are

1. Checkout the SLiCAP repository

2. Install Required SLiCAP Dependencies

3. Install SLiCAP

4. Build the SLiCAP documentation

5. Setup pages - For now this is verbatium of 

6. upload artifact
