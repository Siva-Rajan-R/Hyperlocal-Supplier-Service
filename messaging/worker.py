from .main import RabbitMQMessagingConfig,ExchangeType
from .controllers.controller import ConsumersHandler
import asyncio

async def worker():
    rabbitmq_conn=await RabbitMQMessagingConfig.get_rabbitmq_connection()
    rabbitmq_msg_obj=RabbitMQMessagingConfig(rabbitMQ_connection=rabbitmq_conn)

    # Exchanges
    exchanges=[
        {'name':'purchase.purchase.suppliers.exchange','exc_type':ExchangeType.TOPIC},
        {'name':'products.purchase.suppliers.exchange','exc_type':ExchangeType.TOPIC}
    ]

    for exchange in exchanges:
        await rabbitmq_msg_obj.create_exchange(name=exchange['name'],exchange_type=exchange['exc_type'])

    # Queues
    queues=[
        {'exc_name':'purchase.purchase.suppliers.exchange','q_name':'purchase.purchase.suppliers.queue','r_key':'purchase.purchase.*.*.v1'},
        {'exc_name':'products.purchase.suppliers.exchange','q_name':'products.purchase.suppliers.queue','r_key':'products.purchase.*.*.v1'}
    ]

    for queue in queues:
        queue=await rabbitmq_msg_obj.create_queue(
            exchange_name=queue['exc_name'],
            queue_name=queue['q_name'],
            routing_key=queue['r_key']
        )

    # Consumers
    consumers=[
        {'q_name':'purchase.purchase.suppliers.queue','handler':ConsumersHandler.main_handler},
        {'q_name':'products.purchase.suppliers.queue','handler':ConsumersHandler.main_handler}
    ]

    for consumer in consumers:
        await rabbitmq_msg_obj.consume_event(queue_name=consumer['q_name'],handler=consumer['handler'])

    await asyncio.Event().wait()

    



    