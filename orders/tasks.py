from celery import shared_task


@shared_task
def send_order_confirmation(order_id):
    return f"Order {order_id} confirmation is ready."