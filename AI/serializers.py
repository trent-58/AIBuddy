from rest_framework import serializers
from .models import AITask, Submission, AIEvaluation


class AITaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITask
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = ["id", "submitted_at", "user"]


class AIEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIEvaluation
        fields = "__all__"
        read_only_fields = ["id", "created_at"]