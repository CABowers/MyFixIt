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
	```
	pip install virtualenv
	Virtualenv venv
	```
	`\. Venv\bin\activate` or `venv\Scripts\activate`

### DOWNLOAD
`git clone https://github.com/CABowers/MyFixIt.git`

### DEPENDENCIES
From inside the MyFixIt directory:
```
pip install -r requirements.txt
pip install flask-ask zappa requests awscli
pip install git+https://github.com/agiddings/pyfixit
```

### INITIAL SETUP
* Create an IAM user in the AWS console
	1. Go to [AWS and open the IAM console](https://console.aws.amazon.com/iam/home#/users). Set up an AWS account if you haven't already
	2. Click the add user button
	3. Name the user zappa-deploy, choose Programmatic access for the Access type, then click the "Next: Permissions" button.
	4. On the permissions page, click the Attach existing policies directly option.
	5. A large list of policies is displayed. Locate the AdministratorAccess policy, select its checkbox, then click the "Next: Review"button.
	6. Finally, review the information that displays, and click the Create User button.
	7. Once the user is created, its Access key ID and Secret access key are displayed (click the Show link next to the Secret access key to unmask it). You will need these later. Also, treat these with the same care as you do with your AWS username and password because they have the same privileges. 
	8. Type `aws configure` in the console (virtual environment)
	9. Follow the prompts to input your Access key ID and Secret access key.
	10. For Default region name, type: us-east-1.
	11. For Default output format accept the default by hitting the Enter key.
	12. The aws configure command installs credentials and configuration in an .aws directory inside your home directory. Zappa knows how to use this configuration to create the AWS resources it needs to deploy Flask-Ask skills to Lambda.
	
* Configure Zappa (in terminal)
	1. Type the following. Select all default configurations. 
	```
	zappa init
	zappa deploy dev
	zappa update dev
	```
	
	2. After your deploy copy the endpoint it displays. It should look like this: https://mcgalgvft5.execute-api.us-east-1.amazonaws.com/dev
* Set up Alexa Skill
	1. Go to the [Amazons Developer portal and go to the Alexa tab and Alexa Skill Kit](https://developer.amazon.com/edw/home.html#/skills). Click add new skill.
	2. On the skill information tab make "MyFixIt" the name and "my fix it" the invocation name.
	3. Click Save. Then Next.
	4. Copy over the Intent Schema and Sample Utterances from the corresponding files to the cooressponding slots.
	5. From Custom_Slot file, the first line goes at the type and all other lines are the values. Enter in this information then click save and next.
	6. Select HTTPS as the Service Endpoint Type. You might have noticed the other option AWS Lambda ARN seems more appropriate, but since Zappa uses API gateways for WSGI emulation, we're going to select HTTPS here.
	7. In the Default space enter in the lambda endpoint configured in the previous steps. This was outputed after the command Zappa update.
	8. Select No for geographical regions. Click the Next button.
	9. On the SSL Certificate section select the option that reads: My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority.	

### BUILD
After any code change:
```
zappa update
```
	
### INSTALLATION
None, automatically done by Amazon and Zappa	

### RUNNING APPLICATION
Test through Developer Portal or on Alexa enabled device. 
Type "Open my fix it" in the enter utterance input on the test page of the developer website
or say "Alexa, Open my fix it" to an echo device.
