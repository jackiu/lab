from troposphere import Template
from troposphere.cloudformation import Stack

t = Template()


t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")


t.add_resource(Stack("Networking", TemplateURL="",Parameters={}))
t.add_resource(Stack("IAM", TemplateURL="",Parameters={}))
t.add_resource(Stack("Firewall", TemplateURL="",Parameters={}))
t.add_resource(Stack("Bastion", TemplateURL="",Parameters={}))
t.add_resource(Stack("WebTier", TemplateURL="",Parameters={}))
t.add_resource(Stack("AppTier", TemplateURL="",Parameters={}))
t.add_resource(Stack("DBTier", TemplateURL="",Parameters={}))

file = open('main.json','w')
file.write(t.to_json())


