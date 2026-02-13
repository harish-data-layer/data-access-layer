
// SAP Table Structures
// Mapping to standard SAP ECC / S4HANA tables

export interface SAP_LFA1 {
    LIFNR: string; // Vendor Account Number
    NAME1: string; // Name 1
    NAME2?: string; // Name 2
    ORT01?: string; // City
    PSTLZ?: string; // Postal Code
    STRAS?: string; // Street
    LAND1?: string; // Country Key
    TELF1?: string; // First telephone number
    STCD1?: string; // Tax Number 1
    STCD2?: string; // Tax Number 2
    ERDAT?: string; // Date on which the record was created
    SPERR?: string; // Central posting block
    LOEVM?: string; // Central Deletion Flag
}

export interface SAP_EKKO {
    EBELN: string; // Purchasing Document Number
    BUKRS: string; // Company Code
    BSTYP: string; // Purchasing Document Category
    BSART: string; // Purchasing Document Type
    LIFNR: string; // Vendor Account Number
    EKORG: string; // Purchasing Organization
    EKGRP: string; // Purchasing Group
    WAERS: string; // Currency Key
    AEDAT: string; // Date on which the record was created
}

export interface SAP_EKPO {
    EBELN: string; // Purchasing Document Number
    EBELP: string; // Item Number of Purchasing Document
    LOEKZ?: string; // Deletion Indicator in Purchasing Document
    MATNR?: string; // Material Number
    TXZ01?: string; // Short Text
    MENGE: string; // Purchase Order Quantity
    MEINS: string; // Purchase Order Unit of Measure
    NETPR: string; // Net Price in Purchasing Document (in Document Currency)
    PEINH: string; // Price Unit
}

export interface SAP_BAPIRET2 {
    TYPE: 'S' | 'E' | 'W' | 'I' | 'A'; // Message type: S Success, E Error, W Warning, I Info, A Abort
    ID: string; // Message Class
    NUMBER: string; // Message Number
    MESSAGE: string; // Message Text
    LOG_NO?: string; // Application log: log number
    LOG_MSG_NO?: string; // Application log: Internal message serial number
    MESSAGE_V1?: string; // Message Variable
    MESSAGE_V2?: string; // Message Variable
    MESSAGE_V3?: string; // Message Variable
    MESSAGE_V4?: string; // Message Variable
    PARAMETER?: string; // Parameter Name
    ROW?: number; // Row in Parameter
    FIELD?: string; // Field in Parameter
}
