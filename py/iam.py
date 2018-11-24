from troposphere.iam import InstanceProfile, Role, Policy
from troposphere import Ref, Template, Output, Parameter, Join, GetAtt, Export, Name
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

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(Parameter("RandomString", Description="RandomString", Type="String", Default="123"))



joinClause = Join("-", [Ref("AWS::StackName"), "InstanceProfileArn"])
exp = Export(Name(joinClause))

t.add_output(Output("InstanceProfile",Value=GetAtt(instanceProfile,"Arn"),Export=exp))

file = open('iam.json','w')
file.write(t.to_json())



