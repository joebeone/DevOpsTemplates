"""Generating a CloudFormation Template"""

from troposphere import (
 Base64,
 ec2,
 GetAtt,
 Join,
 Output,
 Parameter,
 Ref,
 Template
)

from ipaddress import ip_network
from ipify import get_ip


ApplicationName = 'HelloWorld'
ApplicationPort = "3000"
GithubAccount = "joebeone"
GithubAnsibleURL = "https://github.com/{}/ansible.git".format(GithubAccount)
PublicCidrIp = str(ip_network(get_ip()))
AnsiblePullCmd = \
"/usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
    GithubAnsibleURL,
    ApplicationName
    )

user_data = Base64(Join('\n', [
    "#!/bin/bash",
    "yum install --enablerepo=epel -y git"
    "pip install ansible",
     AnsiblePullCmd,
    "echo '*/10 * * * * {}' > etc/cron.d/ansible-pull".format(AnsiblePullCmd),
    "yum install --enablerepo=epel -y nodejs",
    ]))

instance = ec2.Instance(
     "instance",
      ImageId="ami-caaf84af",
      InstanceType="t2.micro",
      SecurityGroups=[Ref("SecurityGroup")],
      KeyName=Ref("KeyPair"),
      UserData=user_data,
      AvailabilityZone=Ref("AZ")
    )

key = Parameter(
    "KeyPair",
     Description="Name of existing EC2 KeyPair for SSH",
     Type="AWS::EC2::KeyPair::KeyName",
     ConstraintDescription="must be the name of an existing EC2 KeyPair",
    )

az = Parameter(
    "AZ",
    Description="Select an Availability Zone for the instance",
    Type="AWS::EC2::AvailabilityZone::Name",
    ConstraintDescription="Must be an existing AZ",
    )


security_group = ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
           IpProtocol="tcp",
           FromPort="22",
           ToPort="22",
           CidrIp=PublicCidrIp,
            ),
        ec2.SecurityGroupRule(
           IpProtocol="tcp",
           FromPort=ApplicationPort,
           ToPort=ApplicationPort,
           CidrIp="0.0.0.0/0",
            ),
        ],
    )



t = Template()
t.add_description("Effective DevOps in AWS: HelloWorld web application")
t.add_parameter(key)
t.add_parameter(az)
t.add_resource(security_group)
t.add_resource(instance)
t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of the instance",
    Value=GetAtt(instance, "PublicIp"),
    ))
t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt(instance, "PublicDnsName"),
        ":", ApplicationPort
        ]),
    ))

print(t.to_json())
