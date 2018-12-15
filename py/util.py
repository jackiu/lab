def createSSMParameter(cfname, name, desc, type, value):
    from troposphere.ssm import Parameter 
    return Parameter(cfname, Name=name, Description=desc, Type=type, 
                    Value=value)