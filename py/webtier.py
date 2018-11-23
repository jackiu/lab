from troposphere import Join, Output
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select


from troposphere.elasticloadbalancing import LoadBalancer
from troposphere.policies import (
    AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
)
from troposphere.ec2 import LaunchTemplate, LaunchTemplateData, IamInstanceProfile
from troposphere.iam import InstanceProfile, Role 

from troposphere.autoscaling import AutoScalingGroup, Metadata

import userdata

ltdata = LaunchTemplateData("WebInstanceTemplateData", 
                            SecurityGroups=[], 
                            UserData=userdata.webUserData,
                            IamInstanceProfile="")


lt  = LaunchTemplate("WebInstanceTemplate", LaunchTemplateName="WebInstanceTemplate", LaunchTemplateData=Ref(ltdata))



everywhereCIDR = "0.0.0.0/0"
localCIDR = "127.0.0.1/32"
blockedEgress = [{
    "CidrIp": localCIDR,
    "IpProtocol": "-1"
}]

vpc = Parameter("VPC", Description="VPC", Type="AWS::EC2::VPC::Id")



t = Template()

t.add_parameter(vpc)
# t.add_resource(closeEgress)

file = open('webtier.json','w')
file.write(t.to_json())