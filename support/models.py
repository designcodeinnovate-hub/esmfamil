# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    STATUS = [
        ("open", "باز"),
        ("in_progress", "در حال بررسی"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_support_tickets",
    )
    subject = models.CharField(max_length=100)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, default="general")
    status = models.CharField(max_length=15, choices=STATUS, default="open")
    admin_reply = models.TextField(blank=True, default="")
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.id} - {self.subject[:30]}"

    def status_display(self):
        return dict(self.STATUS).get(self.status, self.status)


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    body = models.TextField(max_length=2000)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"#{self.ticket_id} {'staff' if self.is_staff else 'user'}"
