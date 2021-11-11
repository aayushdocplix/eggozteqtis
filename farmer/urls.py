from django.urls import path, include
from rest_framework import routers

from farmer.views import FarmerHelpViewSet, FarmerConsultingViewSet, WordpressViewSet, WeatherMapViewSet, \
    FarmerIotEnquiryViewSet, PinWeatherMapViewSet, NotificationViewSet, IotViewSet
from farmer.views.SerializedViews import FarmerViewSet, FarmViewSet, ShedViewSet, FlockBreedViewSet, FlockViewSet, \
    DailyInputViewSet, FarmerSummaryViewSet, FlockSummaryViewSet, FlockGraphViewSet, FeedMedicineViewSet, \
    FarmerOrderViewSet, PartyViewSet, ExpensesViewSet, PostViewSet, PostLikeViewSet, PostCommentViewSet, \
    PostCommentLikeViewSet, NECCCityViewSet, CityNECCRateViewSet, FarmerBannerViewSet, NECCZoneViewSet, \
    FarmerAlertViewSet, FeedFeedIngredientViewSet, FeedFormulationViewSet, FeedIngredientFormulaDataViewSet, \
    FlockFeedFormulationViewSet

app_name = "farmer"
router = routers.DefaultRouter()
router.register('farm', FarmViewSet, basename='farm')
router.register('shed', ShedViewSet, basename='shed')
router.register('flock', FlockViewSet, basename='flock')
router.register('flock_breed', FlockBreedViewSet, basename='flock_breed')
router.register('daily_input', DailyInputViewSet, basename='daily_input')
router.register('farmer_summary', FarmerSummaryViewSet, basename='farmer_summary')
router.register('flock_summary', FlockSummaryViewSet, basename='flock_summary')
router.register('flock_graph', FlockGraphViewSet, basename='flock_graph')
router.register('feed_medicine', FeedMedicineViewSet, basename='feed_medicine')
router.register('feed_ingredient', FeedFeedIngredientViewSet, basename='feed_ingredient')
router.register('feed_formulation', FeedFormulationViewSet, basename='feed_formulation')
router.register('flock_feed_formulation', FlockFeedFormulationViewSet, basename='flock_feed_formulation')
router.register('feed_ingredient_formula_data', FeedIngredientFormulaDataViewSet,
                basename='feed_ingredient_formula_data')
router.register('order', FarmerOrderViewSet, basename='order')
router.register('party', PartyViewSet, basename='party')
router.register('expenses', ExpensesViewSet, basename='expenses')
router.register('post', PostViewSet, basename='post')
router.register('post_like', PostLikeViewSet, basename='post_like')
router.register('post_comment', PostCommentViewSet, basename='post_comment')
router.register('post_comment_like', PostCommentLikeViewSet, basename='post_comment_like')
router.register('necc_city', NECCCityViewSet, basename='necc_city')
router.register('necc_city_rate', CityNECCRateViewSet, basename='necc_city_rate')
router.register('help', FarmerHelpViewSet, basename='help')
router.register('consult', FarmerConsultingViewSet, basename='consult')
router.register('iot_enquiry', FarmerIotEnquiryViewSet, basename='iot_enquiry')
router.register('wordpress', WordpressViewSet, basename='wordpress')
router.register('weather', WeatherMapViewSet, basename='weather')
router.register('weather-pin', PinWeatherMapViewSet, basename='weather-pin')
router.register('banner', FarmerBannerViewSet, basename='banner')
router.register('necc_zone', NECCZoneViewSet, basename='necc_zone')
router.register('alert', FarmerAlertViewSet, basename='alert')
router.register('notification', NotificationViewSet, basename='notification')
router.register('iot-data', IotViewSet, basename='iot-data')
router.register(r'', FarmerViewSet, basename='')

urlpatterns = [
    path('', include(router.urls)),
]
