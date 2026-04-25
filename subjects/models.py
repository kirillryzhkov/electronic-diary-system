# subjects/models.py
from django.db import models


class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название предмета'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['name']

    def __str__(self):
        return self.name