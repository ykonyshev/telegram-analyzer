from typing import List
from analysis.models.Message.MediaDetails.AudioDetails import AudioDetails
from analysis.models.Message.MediaDetails.PhotoDetails import PhotoDetails

MediaDetail = PhotoDetails | AudioDetails
# NOTE: See: https://github.com/BeanieODM/beanie/issues/824
MediaDetails = List[MediaDetail]
