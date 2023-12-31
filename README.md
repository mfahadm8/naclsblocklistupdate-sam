# AIAssistant

### Prerequisites
Make sure to configure and install the following requirements:
- `AWS CLI:` Configure the AWS Command Line Interface (CLI) with your AWS account credentials. Refer to the [AWS CLI Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for detailed instructions about installation and configuration.
### Deployment Command 
```bash
aws cloudformation deploy --template-file template.yaml --stack-name NaclBlocklistUpdateStack --capabilities CAPABILITY_NAMED_IAM
```

### Change to be Made Before Deployment
Change the following parameters in template 
-  `PipelineArtifactsBucketName:` Name of Bucket Globally unique bucket to Store Pipeline Artifacts
-  `FullGitHubRepoId:` GitHub repository Id i.e some-user/my-repo
-  `GitHubBranch:` Trigger Branch Name
-  `ApproverEmail:` Email of the Approver
-  `ConnectionArn:` ARN of the connection to GitHub

Note: Please note that for the first time you have to manually enable the transition for ManualApproval Stage. 
#   n a c l s b l o c k l i s t u p d a t e - s a m  
 