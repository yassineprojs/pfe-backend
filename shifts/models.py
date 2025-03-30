from django.db import models

class Shift(models.Model):
    SHIFT_CHOICES = [
        ('Morning', 'Morning Shift (08:00-16:00)'),
        ('Evening', 'Evening Shift (16:00-24:00)'),
        ('Night', 'Night Shift (00:00-08:00)')
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ]

    name = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)

    def __str__(self):
        return f"{self.get_weekday_display()} {self.name}"

class Planning(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='plannings')
    analyst = models.ForeignKey('users.Analyst', on_delete=models.CASCADE,related_name='plannings')  
    plan_date = models.DateField(db_index=True)

    class Meta:
        unique_together = ['shift', 'analyst', 'plan_date']

    def __str__(self):
        return f"{self.analyst} - {self.shift} on {self.plan_date}"