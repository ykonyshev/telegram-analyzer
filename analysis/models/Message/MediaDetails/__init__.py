from analysis.models.Message.MediaDetails.AudioDetails import AudioDetails
from analysis.models.Message.MediaDetails.PhotoDetails import PhotoDetails

MediaDetail = PhotoDetails | AudioDetails
MediaDetails = list[MediaDetail]
