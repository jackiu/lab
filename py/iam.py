from troposphere.iam import InstanceProfile, Role, Policy
from troposphere import Ref, Template, Output, Parameter
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole

import policies

ec2RolePolicies = ["arn:aws:iam::aws:policy/AmazonS3FullAccess", "arn:aws:iam::aws:policy/AmazonSSMFullAccess"]


ec2Role = Role("Role", 
                AssumeRolePolicyDocument=Policy(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[AssumeRole],
                            Principal=Principal("Service", ["ec2.amazonaws.com"])
                        )
                    ]
                ), 
                RoleName="EC2Role", 
                ManagedPolicyArns=ec2RolePolicies)

instanceProfile = InstanceProfile("EC2InstanceProfile", Roles=[Ref(ec2Role)], InstanceProfileName="EC2InstanceProfile")

t = Template()


t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(Parameter("RandomString", Description="RandomString", Type="String"))


t.add_resource(ec2Role)
t.add_resource(instanceProfile)

t.add_output(Output("InstanceProfile",Value=Ref(instanceProfile)))

file = open('iam.json','w')
file.write(t.to_json())



