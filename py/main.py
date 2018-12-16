from troposphere import Template, GetAtt
from troposphere.cloudformation import Stack

t = Template()


t.add_version('2010-09-09')

t.add_description("""\
Main Stack to call all nested stacks  \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

pubCertArn = "arn:aws:acm:us-west-2:350032182433:certificate/535e204c-72b1-4d92-a45a-a3f0a7005362"
instanceProfileArn = "arn:aws:iam::350032182433:instance-profile/EC2InstanceProfile"
dbUser = "jack"
dbPassword = "11223344"


templateLocation = "https://s3.amazonaws.com/jackiu-hosting/"

t.add_resource(Stack("Networking", TemplateURL=templateLocation+"networking.json", Parameters={ "CIDRPrefix" : "192.168"}))
t.add_resource(Stack("KMS", TemplateURL=templateLocation+"kms.json",Parameters={}))
t.add_resource(Stack("Firewall", TemplateURL=templateLocation+"firewall.json",
                        Parameters={
                                "VPC": GetAtt("Networking", "Outputs.VPC"),
                                "SubnetId5": GetAtt("Networking", "Outputs.Subnet5"),
                                "SubnetId6": GetAtt("Networking", "Outputs.Subnet6")
                                }))
t.add_resource(Stack("Bastion", TemplateURL=templateLocation+"bastion.json", 
                        Parameters={
                                "VPC": GetAtt("Networking", "Outputs.VPC"),
                                "InstanceProfileArn" : instanceProfileArn,
                                "PubSubnet1": GetAtt("Networking", "Outputs.Subnet1"),
                                "PubSubnet2": GetAtt("Networking", "Outputs.Subnet2"),
                                "BastionSG" : GetAtt("Firewall", "Outputs.BastionSG")
                                }))
t.add_resource(Stack("DBTier", TemplateURL=templateLocation+"db.json",
                        Parameters={
                                "DatabaseName" : "poc",
                                "DBUser" : dbUser,
                                "DBPassword" : dbPassword,
                                "VPC": GetAtt("Networking", "Outputs.VPC"),
                                "PrivateSubnetDB1": GetAtt("Networking", "Outputs.Subnet7"),
                                "PrivateSubnetDB2": GetAtt("Networking", "Outputs.Subnet8"),
                                "DBKeyArn" : GetAtt("KMS", "Outputs.DbKeyArn"),
                                "DBSG" : GetAtt("Firewall", "Outputs.DBSG")
                                }))
t.add_resource(Stack("ParameterStore", TemplateURL=templateLocation+"parameterstore.json",
                        Parameters={
                                "DBUser": dbUser,
                                "DBPassword": dbPassword,
                                "DBEndpointURL": GetAtt("DBTier", "Outputs.EndPointAddress"),
                                "SecretManagerKeyArn" : GetAtt("KMS", "Outputs.SecretManagerKeyArn"),
                                "CCEncryptionKeyArn" : GetAtt("KMS", "Outputs.CCEncryptionKeyArn"),
                                }))


t.add_resource(Stack("AppTier", TemplateURL=templateLocation+"apptier.json",
                        Parameters={
                                "PubCertARN": pubCertArn,
                                "VPC": GetAtt("Networking", "Outputs.VPC"),
                                "SubnetId3": GetAtt("Networking", "Outputs.Subnet3"),
                                "SubnetId4" : GetAtt("Networking", "Outputs.Subnet4"),
                                "SubnetId5" : GetAtt("Networking", "Outputs.Subnet5"),
                                "SubnetId6" : GetAtt("Networking", "Outputs.Subnet6"),
                                "InstanceProfileArn" : instanceProfileArn,
                                "AppInstanceSG" : GetAtt("Firewall", "Outputs.AppInstanceSG"),
                                "AppALBSG" : GetAtt("Firewall", "Outputs.AppALBSG")
                                }))

t.add_resource(Stack("WebTier", TemplateURL=templateLocation+"webtier.json", 
                        Parameters={
                                "PubCertARN": pubCertArn,
                                "VPC": GetAtt("Networking", "Outputs.VPC"),
                                "SubnetId1": GetAtt("Networking", "Outputs.Subnet1"),
                                "SubnetId2" : GetAtt("Networking", "Outputs.Subnet2"),
                                "SubnetId3" : GetAtt("Networking", "Outputs.Subnet3"),
                                "SubnetId4" : GetAtt("Networking", "Outputs.Subnet4"),
                                "InstanceProfileArn" : instanceProfileArn,
                                "WebInstanceSG" : GetAtt("Firewall", "Outputs.WebInstanceSG"),
                                "WebALBSG" : GetAtt("Firewall", "Outputs.WebALBSG")
                                }))

file = open('main.json','w')
file.write(t.to_json())


