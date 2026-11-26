from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, AdmissionViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")
router.register("admissions", AdmissionViewSet, basename="admission")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
urlpatterns = router.urls
