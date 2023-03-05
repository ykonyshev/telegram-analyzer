from package.models.Message.MediaDetails.AudioDetails import AudioDetails
from package.models.Message.MediaDetails.PhotoDetails import PhotoDetails

MediaDetails = list[PhotoDetails | AudioDetails]
