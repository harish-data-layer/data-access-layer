import winston from 'winston';
// import 'winston-daily-rotate-file';

const LOG_LEVEL = process.env.LOG_LEVEL || 'info';

const format = winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json() // Enterprise standard: JSON logs
);

export const createLogger = (service: string) => {
    return winston.createLogger({
        level: LOG_LEVEL,
        format,
        defaultMeta: {
            service: process.env.SERVICE_NAME || 'tranai-dal',
            component: service,
            env: process.env.NODE_ENV,
        },
        transports: [
            // Console logging for local dev/k8s stdout
            new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    winston.format.simple()
                ),
            })
        ],
    });
};

export const logger = createLogger('API'); // Default logger
