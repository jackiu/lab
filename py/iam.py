from troposphere.iam import InstanceProfile, Role, Policy
from troposphere import Ref, Template, Output, Parameter, Join, GetAtt, Export, Name, Tags, Sub
from troposphere.kms import Key, Alias

from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole

import policies

ec2RolePolicies = ["arn:aws:iam::aws:policy/AmazonS3FullAccess", "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"]

t = Template()

ec2Role = t.add_resource(
                Role("Role", 
                AssumeRolePolicyDocument=Policy(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[AssumeRole],
                            Principal=Principal("Service", ["ec2.amazonaws.com"])
                        )
                    ]
                ), 
                RoleName="GenericEC2Role", 
                ManagedPolicyArns=ec2RolePolicies))

instanceProfile = t.add_resource(
                InstanceProfile("EC2InstanceProfile", Roles=[Ref(ec2Role)], InstanceProfileName="EC2InstanceProfile")
                )


dbKey = t.add_resource(
                Key("DBKey", Description="Key for Aurora Postgres Encryption At Rest", EnableKeyRotation=True, 
                    KeyPolicy=Sub(policies.dbKMSKeyPolicy), Tags=Tags(Application=Ref("AWS::StackName")) )
                )
t.add_resource( 
        Alias("DBKeyAlias", AliasName="alias/AuroraPostgresKey", TargetKeyId=Ref(dbKey)))


secretManagerKey = t.add_resource(
                Key("SecretManagerKey", Description="Key for Secret Manger Key Encryption ", EnableKeyRotation=True, 
                    KeyPolicy=Sub(policies.secretManagerKeyPolicy), Tags=Tags(Application=Ref("AWS::StackName")) )
                )
t.add_resource( 
        Alias("SecretManagerKeyAlias", AliasName="alias/SecretManagerKey", TargetKeyId=Ref(secretManagerKey)))

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(Parameter("RandomString", Description="RandomString", Type="String", Default="123"))



t.add_output(Output("InstanceProfile",Value=GetAtt(instanceProfile,"Arn"),
                Export=Export(Name(Join("-", [Ref("AWS::StackName"), "InstanceProfileArn"])))))

t.add_output(Output("DbKeyArn",Value=GetAtt(dbKey,"Arn"),
                Export=Export(Name(Join("-", [Ref("AWS::StackName"), "DBKeyArn"])))))
                
t.add_output(Output("SecretManagerKeyArn",Value=GetAtt(secretManagerKey,"Arn"),
                Export=Export(Name(Join("-", [Ref("AWS::StackName"), "SecretManagerKeyArn"])))))




file = open('iam.json','w')
file.write(t.to_json())



