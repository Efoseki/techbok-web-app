from rest_framework import serializers

ALLOWED_ENTITY_TYPES = {'student_draft','admission_enquiry','student_record','admission_application','enrollment_record','attendance_mark','assessment_answer','assessment_mark','finance_draft'}
class SyncEventInputSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    device_id = serializers.CharField(max_length=80)
    queued_by = serializers.IntegerField(required=False)
    entity_type = serializers.ChoiceField(choices=sorted(ALLOWED_ENTITY_TYPES))
    operation = serializers.ChoiceField(choices=['upsert','delete'], default='upsert')
    payload = serializers.JSONField()
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()

    def validate_payload(self, value):
        import json
        if not isinstance(value, dict): raise serializers.ValidationError('Payload must be a JSON object.')
        if len(json.dumps(value, ensure_ascii=False)) > 20000: raise serializers.ValidationError('Each payload must be 20 KB or smaller.')
        return value

class SyncBatchSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=80)
    events = SyncEventInputSerializer(many=True, allow_empty=False, max_length=100)
