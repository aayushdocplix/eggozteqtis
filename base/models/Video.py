from django.db import models


class VideoCategory(models.Model):
    category = models.CharField(max_length=254)

    def __str__(self):
        return self.category


class Video(models.Model):
    video_url = models.CharField(max_length=254)
    image_url = models.CharField(max_length=254)
    description = models.CharField(max_length=254)
    videoCategory = models.ForeignKey(VideoCategory, on_delete=models.DO_NOTHING, null=True, blank=True,related_name='videos')

    def __str__(self):
        return self.description


class VideoTag(models.Model):
    tag = models.CharField(max_length=254)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True,related_name='video_tags')

    def __str__(self):
        return self.tag
