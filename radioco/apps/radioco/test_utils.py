# Radioco - Broadcasting Radio Recording Scheduling system.
# Copyright (C) 2014  Iago Veloso Abalo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import datetime

import pytz
import recurrence
from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from radioco.apps.programmes.models import Programme, Episode, Podcast, Role, CONTRIBUTOR
from radioco.apps.schedules.models import Calendar, Schedule


SPAIN_TZ = pytz.timezone('Europe/Madrid')


def spain_tz():
    return SPAIN_TZ


def create_test_data():
    # Example schedule
    calendar, created = Calendar.objects.get_or_create(
        name='Example', is_active=True)

    # Another example schedule
    Calendar.objects.get_or_create(
        name='Another example', is_active=False)

    # Programme 1
    synopsis = '''
        Lorem Ipsum is simply dummy text of the printing and typesetting industry.
        Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
        when an unknown printer took a galley of type and scrambled it to make a type specimen book.
    '''
    programme, created = Programme.objects.get_or_create(
        name='Morning News', defaults={
            'synopsis': synopsis,
            'language': 'en',
            'photo': 'defaults/example/radio_1.jpg',
            'current_season': 1,
            'category': 'News & Politics',
            '_runtime': 60,
        }
    )

    Schedule.objects.get_or_create(
        programme=programme,
        type='L',
        calendar=calendar,
        recurrences=recurrence.Recurrence(rrules=[recurrence.Rule(recurrence.DAILY)]),
        start_dt=pytz.utc.localize(datetime.datetime(2015, 1, 1, 8, 0, 0)))

    for number in range(1, 4):
        episode, created = Episode.objects.get_or_create(
            title='Episode %s' % number,
            programme=programme,
            summary=synopsis,
            season=1,
            number_in_season=number,
        )
        if number == 1:
            Podcast.objects.get_or_create(
                episode=episode,
                url='https://archive.org/download/Backstate_Wife/1945-08-10_-_1600_-_Backstage_Wife_-_Mary_And_Larry_See_A_Twenty_Year_Old_Portrait_That_Looks_Exactly_Like_Mary_-_32-22_-_14m13s.mp3',
                mime_type='audio/mp3',
                length=0,
                duration=853
            )

    for username_counter in range(1, 6):
        titles = ['', 'Mark Webber', 'Paul Jameson', 'Laura Sommers', 'Martin Blunt', 'John Smith']
        user, created = User.objects.get_or_create(
            username='user_%s' % username_counter,
            defaults={
                'first_name': titles[username_counter]
            }
        )
        user.userprofile.bio = synopsis
        user.userprofile.avatar = 'defaults/example/user_%s.jpg' % username_counter
        user.userprofile.display_personal_page = True
        user.userprofile.save()

        Role.objects.get_or_create(
            person=user,
            programme=programme,
            defaults={
                'role': CONTRIBUTOR,
                'description': synopsis,
            }
        )

    # Programme 2
    programme, created = Programme.objects.get_or_create(
        name='Classic hits',
        defaults={
            'synopsis': synopsis,
            'language': 'en',
            'photo': 'defaults/example/radio_5.jpg',
            'current_season': 7,
            'category': 'News & Politics',
            '_runtime': 60
        }
    )

    Schedule.objects.get_or_create(
        programme=programme,
        type='L',
        calendar=calendar,
        recurrences=recurrence.Recurrence(rrules=[recurrence.Rule(recurrence.DAILY)]),
        start_dt=pytz.utc.localize(datetime.datetime(2015, 1, 1, 14, 0, 0)))

    for number in range(1, 6):
        Episode.objects.create(
            title='Episode %s' % number,
            programme=programme,
            summary=synopsis,
            season=7,
            number_in_season=number,
        )


    # Programme 3 - 6
    titles = ['Places To Go', 'The best wine', 'Local Gossips']
    for programme_counter in range(3):

        start_dt = pytz.utc.localize(
            datetime.datetime(2015, 1, 1, 10, 0, 0) + datetime.timedelta(hours=programme_counter)
        )
        programme, created = Programme.objects.get_or_create(
            name=titles[programme_counter],
            defaults={
                'synopsis': synopsis,
                'language': 'en',
                'photo': 'defaults/example/radio_%s.jpg' % str(programme_counter + 2),
                'current_season': 7,
                'category': 'News & Politics',
                '_runtime': 60
            }
        )

        Schedule.objects.get_or_create(
            programme=programme,
            type='L',
            calendar=calendar,
            recurrences=recurrence.Recurrence(rrules=[recurrence.Rule(recurrence.DAILY)]),
            start_dt=start_dt)

        if created:
            for season in range(1, 8):
                for number in range(1, 6):
                    Episode.objects.create(
                        title='Episode %s' % number,
                        programme=programme,
                        summary=synopsis,
                        season=season,
                        number_in_season=number,
                    )

    for programme in Programme.objects.all():
        programme.rearrange_episodes(pytz.utc.localize(datetime.datetime(1970, 1, 1)), Calendar.get_active())


class TestDataMixin(object):
    @classmethod
    def setUpTestData(cls):
        create_test_data()
        cls.programme = Programme.objects.filter(name="Classic hits").get()
        cls.schedule = cls.programme.schedule_set.first()
        cls.calendar = cls.schedule.calendar
        cls.episode = cls.programme.episode_set.first()
        cls.another_calendar = Calendar.objects.create(name="Another")
        cls.another_calendar.schedule_set.add(Schedule(
            programme=cls.programme,
            type='S',
            start_dt=pytz.utc.localize(datetime.datetime(2015, 1, 6, 16, 30, 0))))