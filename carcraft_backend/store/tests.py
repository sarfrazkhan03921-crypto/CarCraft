from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from store.models import (
    CarMake, CarModel, Category, Brand, Product,
    WorkshopService, Cart, CartItem, Order, Coupon,
    VehicleBooking, TestDriveAppointment
)

User = get_user_model()


class CarCraftApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed test user
        self.user = User.objects.create_user(
            username='testdriver',
            email='driver@example.com',
            password='Password123!',
            first_name='Rohan',
            last_name='Verma'
        )

        # Seed Car Make & Model
        self.make = CarMake.objects.create(name='Hyundai', country='South Korea')
        self.model = CarModel.objects.create(
            make=self.make,
            name='Creta',
            body_type='SUV',
            year_start=2024
        )

        # Seed Category & Brand & Product
        self.category = Category.objects.create(name='Engine Parts', icon='Wrench')
        self.brand = Brand.objects.create(name='Castrol')
        self.product = Product.objects.create(
            name='Castrol EDGE 5W-30',
            sku='CC-ENG-TEST',
            category=self.category,
            brand=self.brand,
            price=Decimal('899.00'),
            discount_price=Decimal('749.00'),
            stock=25
        )

        # Seed Workshop Service
        self.service = WorkshopService.objects.create(
            name='Engine Diagnostic Tune-Up',
            short_description='Full engine diagnostic check',
            description='Detailed electronic sensor and spark inspection',
            base_price=Decimal('1499.00'),
            estimated_duration_hours=Decimal('2.5')
        )

        # Seed Coupon
        self.coupon = Coupon.objects.create(
            code='CARCRAFT10',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            is_active=True
        )

    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('status'), 'operational')

    def test_user_registration(self):
        payload = {
            'email': 'newuser@example.com',
            'first_name': 'Amit',
            'last_name': 'Sharma',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'phone': '9876543210'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.json())
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_login(self):
        payload = {
            'email': 'driver@example.com',
            'password': 'Password123!'
        }
        response = self.client.post('/api/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertIn('access', data['tokens'])

    def test_vehicle_list_and_detail(self):
        # List
        res_list = self.client.get('/api/vehicles/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        vehicles = res_list.json()
        self.assertTrue(len(vehicles) >= 1)

        # Detail
        res_detail = self.client.get(f'/api/vehicles/{self.model.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.json()['name'], 'Creta')

    def test_product_list_and_detail(self):
        # List
        res_list = self.client.get('/api/products/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        # Detail
        res_detail = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.json()['sku'], 'CC-ENG-TEST')

    def test_authenticated_cart_flow(self):
        self.client.force_authenticate(user=self.user)

        # Add item to cart
        add_res = self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2}, format='json')
        self.assertIn(add_res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # View cart
        view_res = self.client.get('/api/cart/')
        self.assertEqual(view_res.status_code, status.HTTP_200_OK)
        cart_data = view_res.json()
        self.assertEqual(cart_data['total_items'], 2)

        # Place order
        order_res = self.client.post('/api/orders/', {
            'full_name': 'Rohan Verma',
            'phone': '9876543210',
            'shipping_address': 'Sector 62, Noida, Uttar Pradesh',
            'payment_method': 'cod',
            'coupon_code': 'CARCRAFT10'
        }, format='json')
        self.assertEqual(order_res.status_code, status.HTTP_201_CREATED)
        order_data = order_res.json()
        self.assertTrue('order' in order_data or 'order_number' in order_data)

    def test_service_appointment_booking(self):
        payload = {
            'service_id': self.service.id,
            'vehicle_info': 'Hyundai Creta SX',
            'registration_number': 'DL04AB9999',
            'booking_date': '2026-11-15',
            'time_slot': '10:00 AM - 12:00 PM',
            'notes': 'Periodic servicing and oil check'
        }
        res = self.client.post('/api/service-appointments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_reference', res.json())

    def test_vehicle_booking_endpoint(self):
        payload = {
            'vehicle_model_id': self.model.id,
            'vehicle_name': 'Hyundai Creta 2024',
            'full_name': 'Kunal Sen',
            'phone': '9123456780',
            'email': 'kunal@example.com',
            'city': 'Mumbai',
            'notes': 'Interested in test drive before booking token'
        }
        res = self.client.post('/api/vehicle-bookings/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_reference', res.json())

    def test_test_drive_appointment_endpoint(self):
        payload = {
            'vehicle_model_id': self.model.id,
            'vehicle_name': 'Hyundai Creta 2024',
            'full_name': 'Vikram Rathore',
            'phone': '9988776655',
            'preferred_date': '2026-11-20',
            'time_slot': '02:00 PM - 04:00 PM',
            'notes': 'Would like to test automatic transmission on highway'
        }
        res = self.client.post('/api/test-drives/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_reference', res.json())

    def test_dashboard_stats(self):
        res = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertIn('total_vehicles', data)
        self.assertIn('total_products', data)
        self.assertIn('total_revenue', data)

    def test_login_via_username_and_phone(self):
        # Update user with phone
        self.user.phone = '9876543210'
        self.user.save()

        # Login with username
        res_user = self.client.post('/api/auth/login/', {'email': 'testdriver', 'password': 'Password123!'}, format='json')
        self.assertEqual(res_user.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', res_user.json())

        # Login with phone
        res_phone = self.client.post('/api/auth/login/', {'email': '9876543210', 'password': 'Password123!'}, format='json')
        self.assertEqual(res_phone.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', res_phone.json())

    def test_cart_string_product_id_and_isolation(self):
        user_b = User.objects.create_user(
            username='user_b',
            email='user_b@example.com',
            password='Password123!',
            first_name='Karan'
        )

        # User A adds catalog item with string ID
        self.client.force_authenticate(user=self.user)
        add_res = self.client.post('/api/cart/items/', {
            'product_id': 'part-engine-oil',
            'name': 'Premium Engine Oil',
            'price': '2499.00',
            'category': 'ENGINE',
            'quantity': 1
        }, format='json')
        self.assertIn(add_res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        cart_a = self.client.get('/api/cart/').json()
        self.assertEqual(cart_a['total_items'], 1)

        # User B logs in and views cart - must be empty and isolated!
        self.client.force_authenticate(user=user_b)
        cart_b = self.client.get('/api/cart/').json()
        self.assertEqual(cart_b['total_items'], 0)
