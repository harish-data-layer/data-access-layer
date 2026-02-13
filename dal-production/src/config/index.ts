import dotenv from 'dotenv';
dotenv.config();

export const config = {
    env: process.env.NODE_ENV || 'production',
    port: parseInt(process.env.PORT || '3000', 10),
    db: {
        url: process.env.DATABASE_URL
    },
    kafka: {
        clientId: process.env.KAFKA_CLIENT_ID || 'tranai-dal-prod',
        brokers: (process.env.KAFKA_BROKERS || 'kafka:9092').split(','),
        groupId: process.env.KAFKA_GROUP_ID || 'tranai-dal-consumers'
    },
    sap: {
        odata: {
            baseUrl: process.env.SAP_ODATA_URL,
            username: process.env.SAP_ODATA_USER,
            password: process.env.SAP_ODATA_PASSWORD,
            client: process.env.SAP_CLIENT || '100'
        },
        rfc: {
            ashost: process.env.SAP_ASHOST,
            sysnr: process.env.SAP_SYSNR || '00',
            sysid: process.env.SAP_SYSID,
            user: process.env.SAP_USER,
            passwd: process.env.SAP_PASSWD,
            lang: process.env.SAP_LANG || 'EN'
        }
    },
    jwtSecret: process.env.JWT_SECRET || 'dev_secret'
};
