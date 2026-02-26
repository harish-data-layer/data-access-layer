import { Kafka, Producer, Consumer, EachMessagePayload, KafkaMessage } from 'kafkajs';
import { config } from '../config';
import { createLogger } from './logger';
import { eventsPublished, eventsProcessed } from './metrics';

const logger = createLogger('kafka');

// Kafka client singleton
let kafka: Kafka;
let producer: Producer;
let consumer: Consumer;

export const getKafkaClient = (): Kafka => {
    if (!kafka) {
        kafka = new Kafka({
            clientId: config.kafka.clientId,
            brokers: config.kafka.brokers,
            retry: {
                initialRetryTime: 100,
                retries: 8,
            },
        });

        logger.info('Kafka client initialized', { brokers: config.kafka.brokers });
    }

    return kafka;
};

export const getProducer = async (): Promise<Producer> => {
    if (!producer) {
        const kafka = getKafkaClient();
        producer = kafka.producer();

        await producer.connect();
        logger.info('Kafka producer connected');
    }

    return producer;
};

export const getConsumer = async (): Promise<Consumer> => {
    if (!consumer) {
        const kafka = getKafkaClient();
        consumer = kafka.consumer({ groupId: config.kafka.groupId });

        await consumer.connect();
        logger.info('Kafka consumer connected');
    }

    return consumer;
};

// Event publishing service
export class EventPublisher {
    private producer: Producer | null = null;
    private isAvailable: boolean = false;

    async initialize() {
        try {
            this.producer = await getProducer();
            this.isAvailable = true;
            logger.info('Kafka producer initialized successfully');
        } catch (error) {
            logger.warn('Kafka producer initialization failed - events will not be published', { error });
            this.isAvailable = false;
        }
    }

    async publishEvent(topic: string, event: any): Promise<void> {
        if (!this.producer) {
            await this.initialize();
        }

        try {
            const message = {
                key: event.eventId || event.id,
                value: JSON.stringify(event),
                headers: {
                    'event-type': event.eventType || 'UNKNOWN',
                    'correlation-id': event.correlationId || '',
                    'timestamp': new Date().toISOString(),
                },
            };

            await this.producer!.send({
                topic,
                messages: [message],
            });

            eventsPublished.inc({ event_type: event.eventType || 'UNKNOWN' });
            logger.debug('Event published', { topic, eventId: event.eventId });
        } catch (error) {
            logger.error('Failed to publish event', { topic, error });
            throw error;
        }
    }

    async publishBatch(topic: string, events: any[]): Promise<void> {
        if (!this.producer) {
            await this.initialize();
        }

        try {
            const messages = events.map(event => ({
                key: event.eventId || event.id,
                value: JSON.stringify(event),
                headers: {
                    'event-type': event.eventType || 'UNKNOWN',
                    'correlation-id': event.correlationId || '',
                    'timestamp': new Date().toISOString(),
                },
            }));

            await this.producer!.send({
                topic,
                messages,
            });

            events.forEach(event => {
                eventsPublished.inc({ event_type: event.eventType || 'UNKNOWN' });
            });

            logger.debug('Batch events published', { topic, count: events.length });
        } catch (error) {
            logger.error('Failed to publish batch events', { topic, error });
            throw error;
        }
    }
}

// Event consumer service
export class EventConsumer {
    private consumer: Consumer | null = null;
    private handlers: Map<string, (event: any) => Promise<void>> = new Map();

    async initialize() {
        this.consumer = await getConsumer();
    }

    registerHandler(eventType: string, handler: (event: any) => Promise<void>) {
        this.handlers.set(eventType, handler);
        logger.info('Event handler registered', { eventType });
    }

    async subscribe(topics: string[]) {
        if (!this.consumer) {
            await this.initialize();
        }

        for (const topic of topics) {
            await this.consumer!.subscribe({ topic, fromBeginning: false });
            logger.info('Subscribed to topic', { topic });
        }
    }

    async start() {
        if (!this.consumer) {
            await this.initialize();
        }

        await this.consumer!.run({
            eachMessage: async (payload: EachMessagePayload) => {
                await this.handleMessage(payload);
            },
        });

        logger.info('Event consumer started');
    }

    private async handleMessage(payload: EachMessagePayload) {
        const { topic, partition, message } = payload;

        try {
            const event = JSON.parse(message.value?.toString() || '{}');
            const eventType = message.headers?.['event-type']?.toString() || 'UNKNOWN';

            logger.debug('Processing event', { topic, partition, eventType });

            const handler = this.handlers.get(eventType);
            if (handler) {
                await handler(event);
                eventsProcessed.inc({ event_type: eventType, status: 'success' });
            } else {
                logger.warn('No handler found for event type', { eventType });
                eventsProcessed.inc({ event_type: eventType, status: 'no_handler' });
            }
        } catch (error) {
            logger.error('Failed to process event', { topic, partition, error });
            eventsProcessed.inc({ event_type: 'UNKNOWN', status: 'failure' });
        }
    }

    async stop() {
        if (this.consumer) {
            await this.consumer.disconnect();
            logger.info('Event consumer stopped');
        }
    }
}

// Export singletons
export const eventPublisher = new EventPublisher();
export const eventConsumer = new EventConsumer();

// Graceful shutdown
export const disconnectKafka = async () => {
    if (producer) {
        await producer.disconnect();
        logger.info('Kafka producer disconnected');
    }

    if (consumer) {
        await consumer.disconnect();
        logger.info('Kafka consumer disconnected');
    }
};
