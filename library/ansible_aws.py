#!/usr/bin/python
from ansible.module_utils.basic import *
import boto3
import json
from botocore.exceptions import ClientError
class AwsInstance:
    """AWS Instance for Open """
    def __init__(self,resourceType,availabilityZone,aws_access_key_id,aws_secret_access_key):
        self.client = boto3.client(resourceType,availabilityZone, aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
        self.availabilityZone = availabilityZone

    def __ruturnNone__(self,responseStatus):
        if responseStatus is None:
            return True
        else:
            return False

    def checkInstanceStatus(self,instanceId):
        """ Check Instance is running or stopped, return Value is True if instance is Running otherwise False"""
        response = self.client.describe_instance_status(InstanceIds=[instanceId])
        if response['InstanceStatuses']:
            return response.get('InstanceStatuses')[0].get('InstanceState').get('Name')

    def stopRunningInstance(self,instanceId):
        """Stop instance return Value True otherwise False"""
        self.client.stop_instances(InstanceIds=[instanceId])
        waiter = self.client.get_waiter('instance_stopped')
        instance_stopped = waiter.wait(InstanceIds=[instanceId])
        return self.__ruturnNone__(instance_stopped)

    def removeVolumeFromInstance(self,instanceId,volumeId):
        """ Remove Volume from Instance and Wait for Process to complete and Return Value True/False"""
        response = self.client.detach_volume(VolumeId=volumeId,InstanceId=instanceId)
        waiter = self.client.get_waiter('volume_available')
        volumeAvailable = waiter.wait(VolumeIds=[volumeId])
        return self.__ruturnNone__(volumeAvailable)

    def createVolumeFromSnapshot(self,snapshotId,volumeSize,volumeTag):
        """ Create Volume using Snapshot Id """
        response = self.client.create_volume(AvailabilityZone=self.availabilityZone,Size=volumeSize,VolumeType="gp2",SnapshotId=snapshotId)
        volumeId = response['VolumeId']
        waiter = self.client.get_waiter('volume_available')
        volumeAvailable = waiter.wait(VolumeIds=[volumeId])
        volume = self.__ruturnNone__(volumeAvailable)
        if volume is True:
            self.client.create_tags(Resources=[volumeId],Tags=[{'Key':'Name','Value':volumeTag}])
            return volumeId

    def getLatestSnapshotByVolume(self,volumeId):
        response=self.client.describe_snapshots(Filters=[{'Name': 'volume-id','Values': [volumeId,]},])
        sorted_snapshot=sorted(response['Snapshots'], key=lambda item: item['StartTime'], reverse=True)
        return sorted_snapshot[0]['SnapshotId']

    def attachVolumeInstance(self,volumeId,instanceId,mountPoint):
        response=self.client.attach_volume(VolumeId=volumeId,InstanceId=instanceId,Device=mountPoint)
        waiter = self.client.get_waiter('volume_in_use')
        volumeInUse = waiter.wait(VolumeIds=[volumeId])
        return self.__ruturnNone__(volumeInUse)


    def getImageRootVolume(self,imageId,root=False):
        """Check AMI Image and Return DeviceName VolumeSize SnapshotId and VolumeType"""
        response = self.client.describe_images(ImageIds=[imageId])
        print response
        if response['Images'][0]['ImageId'] is not None:
            deviceNameSize = {}
            for i in response['Images'][0]['BlockDeviceMappings']:
                if i['DeviceName'] == "/dev/sda1" and root is True:
                    return i

    def get_image(self, ami):
        """Check AMI Image and Return DeviceName VolumeSize SnapshotId and VolumeType"""
        valid_ami = False
        response = self.client.describe_images(ImageIds=[ami])
        ImageId = response['Images'][0]['ImageId']
        if ImageId is not None:
            valid_ami = True
            Device_Vol_Size = {}
            Ebs_SnapshotId_ami = {}
            for i in response['Images'][0]['BlockDeviceMappings']:
                if i.has_key('Ebs'):
                    if int(i['Ebs']['VolumeSize']) < 100:
                        Device_Vol_Size[i['DeviceName']] = i['Ebs']['VolumeSize']
                        Ebs_SnapshotId_ami[i['Ebs']['SnapshotId']] = i['Ebs']['VolumeType']
            return Device_Vol_Size, Ebs_SnapshotId_ami, valid_ami
        else:
            print "Unable to find Image id {0}".format(ImageId)

    def check_snapshot_present(self, SnapshotId):
        """Check Volume Snapshot and Return True if Snapshot Valid"""
        valid_snapshot = False
        response = self.client.describe_snapshots(SnapshotIds=[SnapshotId])
        get_SnapshotId = response['Snapshots'][0]['SnapshotId']
        if get_SnapshotId == SnapshotId:
            valid_snapshot = True
            return valid_snapshot

    def set_root_swap_vol(self, SnapShotId, DeviceName, VolumeSize, VolumeType):
        """Set Volume for Instance """
        if VolumeType == "gp2":
            BlockDeviceMappings = {
                "DeviceName": DeviceName,
                "Ebs": {
                    "DeleteOnTermination": True,
                    "SnapshotId": SnapShotId,
                    "VolumeSize": VolumeSize,
                    "VolumeType": VolumeType
                }
            }
        else:
            BlockDeviceMappings = {
                "DeviceName": DeviceName,
                "Ebs": {
                    "DeleteOnTermination": True,
                    "Iops": 300,
                    "SnapshotId": SnapShotId,
                    "VolumeSize": VolumeSize,
                    "VolumeType": VolumeType
                }
            }
        return BlockDeviceMappings

    def setDataVolume(self,volumeId,DeviceName,volumeSize,volumeType):
        snapshotId = self.getLatestSnapshotByVolume(volumeId)
        if snapshotId is not None:
            BlockDeviceMappings =   {
                "DeviceName": DeviceName,
                "Ebs": {
                    "DeleteOnTermination": True,
                    "SnapshotId": snapshotId,
                    "VolumeSize": volumeSize,
                    "VolumeType": volumeType
                }
            }
            return BlockDeviceMappings


    def getPlacement(self,placementName=None):
        """Check ZoneName and return ZoneName"""
        response = self.client.describe_availability_zones(ZoneNames=[placementName])
        ZoneName = response['AvailabilityZones'][0]['ZoneName']
        return ZoneName

    def setPlacement(self,placementName=None):
        """Set ZoneName and return ZoneName Dictionary"""
        if placementName is not None:
            placementSet = {
                "AvailabilityZone": placementName,
                "GroupName": "",
                "Tenancy": "default"
            }
            return placementSet

    def getKeyName(self,keyName):
        """Verifing KeyName and exist return True & otherwise False"""
        response = self.client.describe_key_pairs()
        for keyPair in response.get('KeyPairs',[]):
            if keyPair['KeyName'] is keyName:
                return True
            else:
                return False

    def setKeyName(self,keyName,KeyDir):
        """ Set Key Name and Download to Key File """
        try:
            response = self.client.create_key_pair(KeyName=keyName)
            with open("{0}{1}.{2}".format(KeyDir,keyName,"pem"),"w") as f:
                f.write(response['KeyMaterial'])
            return True
        except (IOError):
            return False

    def setTags(self,resourceId,TagValue, TagName):
        self.client.create_tags(Resources=[resourceId], Tags=[{'Key': TagName, 'Value': TagValue}])
        return None

    def createInstance(self,imageId,instanceType,securityGroupId,blockDeviceMapping,keyName,subnetId,placement,minCount=1,maxCount=1):
        """Create EC2 Instance Using AMI and lauch new instance """
        response = self.client.run_instances(ImageId=imageId,MinCount=minCount,MaxCount=maxCount,KeyName=keyName,SubnetId=subnetId,SecurityGroupIds=[securityGroupId],InstanceType=instanceType,Placement=placement,BlockDeviceMappings=blockDeviceMapping)
        waiter = self.client.get_waiter('instance_status_ok')
        waiting =  waiter.wait(InstanceIds=[response['Instances'][0]['InstanceId']])
        if waiting is None:
            publicIpAddress = (self.client.describe_instances(InstanceIds=[response['Instances'][0]['InstanceId']]))['Reservations'][0]['Instances'][0]['PublicIpAddress']
            return { "instanceId": response['Instances'][0]['InstanceId'], "publicIpAddress" : publicIpAddress }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            regionName=dict(required=True),
            imageId=dict(required=True),
            instanceType=dict(required=True),
            securityGroupId=dict(required=True),
            keyName=dict(required=True),
            rootSize=dict(required=True),
            AvailabilityZone=dict(required=True),
            SubnetId=dict(required=True),
            aws_access_key_id=dict(required=True),
            aws_secret_access_key=dict(required=True),
            tag=dict(required=True,type="dict")
        ))
    if module.params['regionName']:
        aws_access_key_id=module.params['aws_access_key_id']
        aws_secret_access_key=module.params['aws_secret_access_key']
        AWSInstance = AwsInstance('ec2', module.params['regionName'],aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
        if AWSInstance and module.params['imageId']:
            Device_Vol_Size, Ebs_SnapshotId_ami, valid_ami = AWSInstance.get_image(module.params['imageId'])
            BlockDevice=[]
            placement = AWSInstance.setPlacement(placementName=module.params['AvailabilityZone'])
            if Device_Vol_Size:
                if module.params['rootSize']:
                    Device_Vol_Size["/dev/sda1"] = int(module.params['rootSize'])
                for (SnapshotId, VolumeType), (DeviceName, VolumeSize) in zip(Ebs_SnapshotId_ami.items(),
                                                                              Device_Vol_Size.items()):
                    BlockDevice.append(AWSInstance.set_root_swap_vol(SnapShotId=SnapshotId,DeviceName=DeviceName,VolumeSize=VolumeSize,VolumeType=VolumeType))
            if BlockDevice and module.params['instanceType'] and  module.params['securityGroupId']:
                instance = AWSInstance.createInstance(imageId=module.params['imageId'],instanceType=module.params['instanceType'],securityGroupId=module.params['securityGroupId'],subnetId=module.params['SubnetId'],blockDeviceMapping=BlockDevice,keyName=module.params['keyName'],placement=placement)
                if instance:
                    if instance and module.params['tag']:
                        for key in module.params['tag']:
                            tag_details = AWSInstance.setTags(resourceId=instance['instanceId'],TagValue=module.params['tag'][key],TagName=key)
                    module.exit_json(changed=True, meta={'instance': instance})
                else:
                    module.fail_json("failed to create instance")

    else:
        module.fail_json("please provide regionName")


if __name__ == "__main__":
    main()
