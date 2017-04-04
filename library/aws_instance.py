#!/usr/bin/python
import boto3
import botocore.exceptions.ClientError

class AwsInstance:
    """AWS Instance for Open """
    def __init__(self,client,availabilityZone):
        self.client = client
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


    def getImageRootVolume(self,imageId):
        """Check AMI Image and Return DeviceName VolumeSize SnapshotId and VolumeType"""
        response = self.client.describe_images(ImageIds=[imageId])
        if response['Images'][0]['ImageId'] is not None:
            deviceNameSize = {}
            for i in response['Images'][0]['BlockDeviceMappings']:
                deviceNameSize.append(i)
            return deviceNameSize

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
        if placementName is None:
            placementName = self.availabilityZone
        zoneName = self.getPlacement(placementName)
        if zoneName is not None:
            placementSet = {
                "AvailabilityZone": zoneName,
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
        except (IOError,InvalidAMIID.NotFound):
            return False

    def createInstance(self,imageId,instanceType,securityGroupId,blockDeviceMapping,keyName,minCount=1,maxCount=1):
        """Create EC2 Instance Using AMI and lauch new instance """
        response = self.client.run_instances(ImageId=imageId,MinCount=minCount,MaxCount=maxCount,KeyName=keyName,SecurityGroupIds=[securityGroupId],InstanceType=instanceType,Placement=self.placements,BlockDeviceMappings=blockDeviceMapping)
        InstanceId = response['Instances'][0]['InstanceId']
        return InstanceId
