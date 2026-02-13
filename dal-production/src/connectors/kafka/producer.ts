import { Kafka, Producer, CompressionTypes, logLevel } from 'kafkajs';
import { config } from '../../config';
import { createLogger } from '../../utils/logger';

const logger = createLogger('kafka-producer');

export class KafkaProducer {
    private kafka: Kafka | null = null;
    private producer: Producer | null = null;
    private isConnected: boolean = false;

    constructor() {
        try {
            this.kafka = new Kafka({
                clientId: config.kafka.clientId,
                brokers: config.kafka.brokers,
                logLevel: logLevel.ERROR,
                retry: {
                    initialRetryTime: 300,
                    retries: 5
                }
            });

            this.producer = this.kafka.producer({
                allowAutoTopicCreation: true
            });
        } catch (e: any) {
            logger.error(`Failed to initialize Kafka Client: ${e.message}`);
        }
    }

    public async connect(): Promise<void> {
        if (!this.producer) return; // Silent fail
        try {
            if (this.isConnected) return;
            await this.producer.connect();
            this.isConnected = true;
            logger.info('✅ Kafka Producer Connected');
        } catch (error: any) {
            logger.error(`❌ Kafka Connection Failed: ${error.message}`);
            // throw error; // Don't throw to prevent app crash
        }
    }

    public async send(topic: string, key: string, message: object): Promise<void> {
        if (!this.producer) {
            logger.warn('Kafka Producer not initialized. Skipping message.');
            return;
        }

        if (!this.isConnected) {
            // try to reconnect
            await this.connect();
            if (!this.isConnected) return;
        }

        try {
            await this.producer!.send({
                topic,
                compression: CompressionTypes.GZIP,
                messages: [{
                    key,
                    value: JSON.stringify(message),
                    headers: { timestamp: Date.now().toString() }
                }],
            });
            logger.debug(`[Kafka] Sent to ${topic}: Key=${key}`);
        } catch (error: any) {
            logger.error(`[Kafka] Failed to send message to ${topic}: ${error.message}`);
            // throw error;
        }
    }
}

export const eventBus = new KafkaProducer();
