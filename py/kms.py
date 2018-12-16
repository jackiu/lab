# from awacs.aws import Allow, Statement, Principal, PolicyDocument, Action
# from awacs.sts import AssumeRole

from troposphere import Ref, Template, Output, Parameter, Join, GetAtt, Export, Name, Tags, Sub
from troposphere.kms import Key, Alias
from troposphere.iam import InstanceProfile, Role, Policy

import policies

# ec2RolePolicies = ["arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess", "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"]

t = Template()

t.add_version('2010-09-09')

t.add_description("""\
Creates KMS keys
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

            
# ec2Role = t.add_resource(
#                 Role("Role", 
#                 AssumeRolePolicyDocument={
#                     "Version" : "2012-10-17",
#                     "Statement": [ {
#                         "Effect": "Allow",
#                         "Principal": {
#                             "Service": [ "ec2.amazonaws.com" ]
#                         },
#                         "Action": [ "sts:AssumeRole" ]
#                     } ]
#                 },
#                 Policies=[
#                     Policy( 
#                         PolicyDocument= {
#                             "Version": "2012-10-17",
#                             "Statement": [
#                                 {
#                                     "Effect": "Allow",
#                                     "Action": ["ssm:GetParameter","secretsmanager:GetSecretValue"],
#                                     "Resource": "*"
#                                 }
#                             ]
#                         },
#                         PolicyName="AppEC2Policy"
#                     )
#                 ],
#                 RoleName="GenericEC2Role", 
#                 ManagedPolicyArns=ec2RolePolicies))



# instanceProfile = t.add_resource(
#                 InstanceProfile("EC2InstanceProfile", Roles=["GenericEC2Role"], InstanceProfileName="EC2InstanceProfile")
#                 )


dbKey = t.add_resource(
                Key("DBKey", Description="Key for Aurora MYSQL Encryption At Rest", EnableKeyRotation=True, 
                    KeyPolicy=Sub(policies.dbKMSKeyPolicy), Tags=Tags(Application=Ref("AWS::StackName")) )
                )
t.add_resource( 
        Alias("DBKeyAlias", AliasName="alias/AuroraMySQLKey", TargetKeyId=Ref(dbKey)))


secretManagerKey = t.add_resource(
                Key("SecretManagerKey", Description="Key for Secret Manger Key Encryption ", EnableKeyRotation=True, 
                    KeyPolicy=Sub(policies.secretManagerKeyPolicy), Tags=Tags(Application=Ref("AWS::StackName")) )
                )
t.add_resource( 
        Alias("SecretManagerKeyAlias", AliasName="alias/SecretManagerKey", TargetKeyId=Ref(secretManagerKey)))


ccEncryptionKey = t.add_resource(
                Key("CCEncryptionKey", Description="Key for Credit Card Encryption ", EnableKeyRotation=True, 
                    KeyPolicy=Sub(policies.ccEncryptionKeyPolicy), Tags=Tags(Application=Ref("AWS::StackName")) )
                )
t.add_resource( 
        Alias("CreditCardEncryptionKeyAlias", AliasName="alias/CreditCardEncryptionKey", TargetKeyId=Ref(ccEncryptionKey)))





# t.add_output(Output("InstanceProfile",Value=GetAtt(instanceProfile,"Arn"),
#                 Export=Export(Name(Join("-", [Ref("AWS::StackName"), "InstanceProfileArn"])))))

t.add_output(Output("DbKeyArn",Value=GetAtt(dbKey,"Arn")))
                
t.add_output(Output("SecretManagerKeyArn",Value=GetAtt(secretManagerKey,"Arn")))

t.add_output(Output("CCEncryptionKeyArn",Value=GetAtt(ccEncryptionKey,"Arn")))



file = open('kms.json','w')
file.write(t.to_json())



