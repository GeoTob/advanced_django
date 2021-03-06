from django.utils import timezone
from django.db import models

from phonenumber_field.modelfields import PhoneNumberField
from timezone_field import TimeZoneField

from .decorators import named_model


class Person(models.Model):
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254)
    phone_number = PhoneNumberField()
    email = models.EmailField()
    team = models.ForeignKey('Team', related_name='persons')

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


@named_model
class Team(models.Model):
    name = models.CharField(max_length=254, unique=True)
    timezone = TimeZoneField(default='Pacific/Auckland')
    email = models.EmailField()


@named_model
class Project(models.Model):
    name = models.CharField(max_length=254, unique=True)
    teams = models.ManyToManyField('Team', related_name='projects')

    def get_team(self):
        current_time = timezone.now()
        local_times = ((team, current_time.astimezone(team.timezone)) for team in self.teams.all())
        team_working = ((team, 8 < time.hour < 17) for team, time in local_times)
        try:
            return next(team for team, working in team_working if working)
        except StopIteration:
            return None


@named_model
class Site(models.Model):
    name = models.CharField(max_length=254, unique=True)
    project = models.ForeignKey('Project', related_name='sites')


@named_model
class SensorType(models.Model):
    name = models.CharField(max_length=254, unique=True)
    units = models.CharField(max_length=12)


@named_model
class Sensor(models.Model):
    name = models.CharField(max_length=254)
    site = models.ForeignKey('Site')
    type = models.ForeignKey('SensorType')
    warning_upper = models.FloatField()
    warning_lower = models.FloatField()

    class Meta:
        unique_together = ('name', 'site')

    @property
    def warnings(self):
        # Should return True if currently active warnings
        return None


class Measurement(models.Model):
    timestamp = models.DateTimeField()
    sensor = models.ForeignKey('Sensor')
    value = models.FloatField()

    class Meta:
        unique_together = ('timestamp', 'sensor')

    def save(self, *args, **kwargs):
        if self.value > self.sensor.warning_upper or self.value < self.sensor.warning_lower:
            self.raise_alarm()
        self.save(*args, **kwargs)

    def raise_alarm(self):
        team = self.sensor.site.project.get_team()
        if team:
            # Send an email to the team.
            pass
        else:
            # Send an email to the project admins.
            pass
