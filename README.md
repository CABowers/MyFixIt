# MyFixIt

## Release Notes version MyFixIt 1.0
### NEW FEATURES
* Updated help section
* Updated flags section to give flags for guides before the guide is selected
* Updated length of guide section to give the length of a guide after it is selected
### BUG FIXES
* Changed the length of guide to return a range
* Allow user to search for a guide after they have started a guide
### KNOWN BUGS
* Some searches return empty results
	
## Install Guide MyFixIt 1.0 - Non developer
### PRE-REQUISITES
* You must have downloaded the Alexa app on your phone and must be in possession of an Alexa device (Echo, dot, Fire TV, etc.)
### DEPENDENCIES
* None
### DOWNLOAD
* None
### BUILD
* None
### INSTALLATION
* Use the Alexa app to get the myFixIt skill
### RUNNING APPLICATION
* Turn on the Alexa device and say “Alexa, open myfixit”


## Install Guide MyFixIt 1.0 - Developer
### PRE-REQUISITES
* Set up a Amazon Developer account at https://developer.amazon.com/
* Log in or create an account
* Create an Alexa Skill

* Optional but encouraged. These steps will create a virtual environment:
	```Pip install virtualenv
	Virtualenv venv
	\. Venv\bin\activate or venv\Scripts\activate
	```

## DOWNLOAD
`git clone https://github.com/CABowers/MyFixIt.git`

## DEPENDENCIES
```
pip install -r requirements.txt
pip install flask-ask zappa requests awscli (Might not need)
pip install git+https://github.com/agiddings/pyfixit
```
	
## BUILD
* Create an IAM user in the AWS console
	1. First you will need to have an Amazon account
	2. Open the IAM console
	3. Click the add user button
	4. Name the user zappa-deploy, choose Programmatic access for the Access type, then click the "Next: Permissions" button.
	5. On the permissions page, click the Attach existing policies directly option.
	6. A large list of policies is displayed. Locate the AdministratorAccess policy, select its checkbox, then click the "Next: Review"button.
	7. Finally, review the information that displays, and click the Create User button.
	8. Once the user is created, its Access key ID and Secret access key are displayed (click the Show link next to the Secret access key to unmask it).
	9. Copy and paste these credentials into a safe location for later reference. You will need these in Deployment Step 2. Also, treat these with the same care as you do with your AWS username and password because they have the same privileges. 
	10. Configure IAM credentials locally
	11. Type aws configure in the console (virtual environment)
	12. Follow the prompts to input your Access key ID and Secret access key.
	13. For Default region name, type: us-east-1.
	14. For Default output format accept the default by hitting the Enter key.
	15. The aws configure command installs credentials and configuration in an .aws directory inside your home directory. Zappa knows how to use this configuration to create the AWS resources it needs to deploy Flask-Ask skills to Lambda.
	
* Configure Zappa (in terminal)
	1. ```
	   zappa init
	   zappa deploy dev
	   zappa update dev
	   ```
	2. After your deploy copy the endpoint it displays. It should look like this: https://mcgalgvft5.execute-api.us-east-1.amazonaws.com/dev
* Link the Lambda to the skill
	1. On the developer portal go to the configuration tab on the skill page
	2. Select HTTPS as the Service Endpoint Type. You might have noticed the other option AWS Lambda ARN seems more appropriate, but since Zappa uses API gateways for WSGI emulation, we're going to select HTTPS here.
	3. In the Default space enter in the lambda endpoint configured in the previous steps.
	4. Select the appropriate geographical region that is closest to your customers checkbox and enter the URL Zappa output during the deploy step in the text field. Click the Next button.
	5. On the SSL Certificate section select the option that reads: My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority
* Go to Developer portal for Alexa skills and update the interaction model (Sample utterances, Intent Schema)
## INSTALLATION
None, automatically done by Amazon and Zappa	
## RUNNING APPLICATION
After any change:
```
zappa update
```
Test through Developer Portal or on Alexa enabled device
