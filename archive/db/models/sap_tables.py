"""
SAP Tables - SQLAlchemy Models with Expanded Columns (30-40 per table)
Schema: sap
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, func, ForeignKey, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import relationship
from db.base import Base

class LFA1(Base):
    """Vendor Master Data (General Section)"""
    __tablename__ = "lfa1"
    __table_args__ = {"schema": "sap"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), nullable=False, unique=True, comment="Vendor Number")
    NAME1 = Column(String(35), nullable=True, comment="Name 1")
    NAME2 = Column(String(35), nullable=True, comment="Name 2")
    NAME3 = Column(String(35), nullable=True, comment="Name 3")
    NAME4 = Column(String(35), nullable=True, comment="Name 4")
    CITY1 = Column(String(35), nullable=True, comment="City")
    POST_CODE1 = Column(String(10), nullable=True, comment="Postal Code")
    STREET = Column(String(35), nullable=True, comment="Street")
    HOUSE_NUM1 = Column(String(10), nullable=True, comment="House Number")
    COUNTRY = Column(String(3), nullable=True, comment="Country Key")
    REGION = Column(String(3), nullable=True, comment="Region (State)")
    TELF1 = Column(String(16), nullable=True, comment="First Telephone Number")
    TELF2 = Column(String(16), nullable=True, comment="Second Telephone Number")
    TELFX = Column(String(31), nullable=True, comment="Fax Number")
    TELTX = Column(String(30), nullable=True, comment="Teletex Number")
    TELX1 = Column(String(30), nullable=True, comment="Telex Number")
    SMTP_ADDR = Column(String(241), nullable=True, comment="E-Mail Address")
    LANGU = Column(String(2), nullable=True, comment="Language Key")
    KTOKK = Column(String(4), nullable=True, comment="Vendor Account Group")
    STCD1 = Column(String(16), nullable=True, comment="Tax Number 1 (GST)")
    STCD2 = Column(String(11), nullable=True, comment="Tax Number 2")
    STCD3 = Column(String(18), nullable=True, comment="Tax Number 3")
    STCEG = Column(String(20), nullable=True, comment="VAT Registration Number")
    BRSCH = Column(String(4), nullable=True, comment="Industry Key")
    KONZS = Column(String(10), nullable=True, comment="Group Key")
    VBUND = Column(String(6), nullable=True, comment="Trading Partner")
    ERDAT = Column(Date, nullable=True, comment="Date on which record was created")
    ERNAM = Column(String(12), nullable=True, comment="Name of Person who Created the Object")
    SPERR = Column(Boolean, default=False, comment="Central Posting Block")
    SPERZ = Column(Boolean, default=False, comment="Payment Block")
    LOEVM = Column(Boolean, default=False, comment="Central Deletion Flag")
    UPDAT = Column(Date, nullable=True, comment="Date of Last Update")
    UPTIM = Column(DateTime, nullable=True, comment="Time of last update")
    MBRSH = Column(String(1), nullable=True, comment="Industry Sector")
    FISKN = Column(String(10), nullable=True, comment="Account number of the master record")
    created_at = Column(DateTime, default=func.now())

    company_codes = relationship("LFB1", back_populates="vendor")
    purchase_orders = relationship("EKKO", back_populates="vendor")
    invoices = relationship("RBKP", back_populates="vendor")


class LFB1(Base):
    """Vendor Master (Company Code)"""
    __tablename__ = "lfb1"
    __table_args__ = (
        UniqueConstraint("LIFNR", "BUKRS", name="lfb1_lifnr_bukrs_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"), nullable=False, comment="Vendor Number")
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    PERNR = Column(String(8), nullable=True, comment="Personnel Number")
    ERDAT = Column(Date, nullable=True, comment="Date on which record was created")
    ERNAM = Column(String(12), nullable=True, comment="Name of Person who Created the Object")
    SPERR = Column(Boolean, default=False, comment="Posting block for company code")
    LOEVM = Column(Boolean, default=False, comment="Deletion Flag for Company Code")
    AKONT = Column(String(10), nullable=True, comment="Reconciliation Account")
    BEGRU = Column(String(4), nullable=True, comment="Authorization Group")
    VZSKZ = Column(String(2), nullable=True, comment="Interest calculation indicator")
    ZTERM = Column(String(4), nullable=True, comment="Terms of Payment Key")
    ZWELS = Column(String(10), nullable=True, comment="List of Respected Payment Methods")
    PAY_TYPE = Column(String(1), nullable=True, comment="Payment Type")
    ZINDT = Column(Date, nullable=True, comment="Date of last interest calculation")
    ZINRT = Column(Integer, nullable=True, comment="Interest calculation frequency")
    EIKTO = Column(String(12), nullable=True, comment="Our account number with the vendor")
    ZSABE = Column(String(15), nullable=True, comment="Clerk at vendor")
    KVERM = Column(String(30), nullable=True, comment="Memo")
    FDGRV = Column(String(10), nullable=True, comment="Planning group")
    BUSAB = Column(String(2), nullable=True, comment="Accounting clerk")
    LNRZE = Column(String(10), nullable=True, comment="Head office account number")
    LNRZB = Column(String(10), nullable=True, comment="Alternative payee")
    ZAMNR = Column(String(10), nullable=True, comment="Ad-hoc agent")
    ZUAWA = Column(String(3), nullable=True, comment="Key for sorting according to assignment numbers")
    ZHBKLS = Column(String(5), nullable=True, comment="House Bank")
    XVERR = Column(Boolean, default=False, comment="Clearing with customer")
    ZGRUP = Column(String(2), nullable=True, comment="Payment grouping")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="company_codes")


class EKKO(Base):
    """Purchasing Document Header"""
    __tablename__ = "ekko"
    __table_args__ = {"schema": "sap"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), nullable=False, unique=True, comment="Purchasing Document Number")
    BUKRS = Column(String(4), nullable=True, comment="Company Code")
    BSTYP = Column(String(1), nullable=True, comment="Purchasing Document Category")
    BSART = Column(String(4), nullable=True, comment="Purchasing Document Type")
    BSAKU = Column(String(1), nullable=True, comment="Control indicator")
    LOEKZ = Column(String(1), nullable=True, comment="Deletion indicator")
    STATU = Column(String(1), nullable=True, comment="Status of Purchasing Document")
    AEDAT = Column(Date, nullable=True, comment="Date on Which Record Was Created")
    ERNAM = Column(String(12), nullable=True, comment="Name of Person who Created the Object")
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"), nullable=True, comment="Vendor Number")
    ZTERM = Column(String(4), nullable=True, comment="Terms of Payment Key")
    ZBD1T = Column(Float, nullable=True, comment="Cash discount days 1")
    ZBD2T = Column(Float, nullable=True, comment="Cash discount days 2")
    ZBD3T = Column(Float, nullable=True, comment="Cash discount days 3")
    ZBD1P = Column(Float, nullable=True, comment="Cash discount percentage 1")
    ZBD2P = Column(Float, nullable=True, comment="Cash discount percentage 2")
    EKORG = Column(String(4), nullable=True, comment="Purchasing Organization")
    EKGRP = Column(String(3), nullable=True, comment="Purchasing Group")
    WAERS = Column(String(5), nullable=True, comment="Currency Key")
    WKURS = Column(Float, nullable=True, comment="Exchange Rate")
    KUFIX = Column(String(1), nullable=True, comment="Indicator: Fix exchange rate")
    BEDAT = Column(Date, nullable=True, comment="Purchasing Document Date")
    KDATB = Column(Date, nullable=True, comment="Start of Validity Period")
    KDATE = Column(Date, nullable=True, comment="End of Validity Period")
    BWVKO = Column(Date, nullable=True, comment="Date of last document update")
    KNUMV = Column(String(10), nullable=True, comment="Number of the document condition")
    RESWK = Column(String(4), nullable=True, comment="Supplying (issuing) plant")
    LPNOH = Column(String(10), nullable=True, comment="Last item number")
    LIBRE = Column(String(1), nullable=True, comment="Release group")
    PROCSTAT = Column(String(2), nullable=True, comment="Processing State")
    NETWR = Column(Float, nullable=True, comment="Net Order Value")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="purchase_orders")
    line_items = relationship("EKPO", back_populates="po_header")


class EKPO(Base):
    """Purchasing Document Item"""
    __tablename__ = "ekpo"
    __table_args__ = (
        UniqueConstraint("EBELN", "EBELP", name="ekpo_ebeln_ebelp_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), ForeignKey("sap.ekko.EBELN"), nullable=False, comment="Purchasing Document Number")
    EBELP = Column(String(5), nullable=False, comment="Item Number of Purchasing Document")
    LOEKZ = Column(String(1), nullable=True, comment="Deletion indicator")
    STATU = Column(String(1), nullable=True, comment="RFQ status")
    AEDAT = Column(Date, nullable=True, comment="Purchasing document item change date")
    TXZ01 = Column(String(40), nullable=True, comment="Short Text")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    EMATN = Column(String(18), nullable=True, comment="Material number")
    BUKRS = Column(String(4), nullable=True, comment="Company Code")
    WERKS = Column(String(4), nullable=True, comment="Plant")
    LGORT = Column(String(4), nullable=True, comment="Storage Location")
    BEDNR = Column(String(10), nullable=True, comment="Requirement Tracking Number")
    MATKL = Column(String(9), nullable=True, comment="Material Group")
    MENGE = Column(Float, nullable=True, comment="Purchase Order Quantity")
    MEINS = Column(String(3), nullable=True, comment="Order Unit")
    BPUMZ = Column(Float, nullable=True, comment="Numerator for Conversion of Order Unit to Base Unit")
    BPUMN = Column(Float, nullable=True, comment="Denominator for Conv. of Order Unit to Base Unit")
    NETPR = Column(Float, nullable=True, comment="Net Price in Purchasing Document")
    PEINH = Column(Float, nullable=True, comment="Price Unit")
    NETWR = Column(Float, nullable=True, comment="Net Order Value in PO Currency")
    BRTWR = Column(Float, nullable=True, comment="Gross order value")
    AGDAT = Column(Date, nullable=True, comment="Deadline for Submission of Quotation")
    WEBAZ = Column(Float, nullable=True, comment="Goods receipt processing time")
    MWSKZ = Column(String(2), nullable=True, comment="Tax on sales/purchases code")
    BONUS = Column(String(2), nullable=True, comment="Settlement Group")
    INSMK = Column(String(1), nullable=True, comment="Stock Type")
    SPINF = Column(Boolean, default=False, comment="Indicator: Update Info Record")
    PRSDR = Column(Boolean, default=False, comment="Print Price")
    BWTAR = Column(String(10), nullable=True, comment="Valuation Type")
    BWTTY = Column(String(1), nullable=True, comment="Valuation Category")
    ABSKZ = Column(String(1), nullable=True, comment="Rejection Indicator")
    created_at = Column(DateTime, default=func.now())

    po_header = relationship("EKKO", back_populates="line_items")


class RBKP(Base):
    """Document Header: Invoice Receipt"""
    __tablename__ = "rbkp"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", name="rbkp_belnr_gjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False, comment="Document Number of an Invoice Document")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BLART = Column(String(2), nullable=True, comment="Document Type")
    BLDAT = Column(Date, nullable=True, comment="Document Date in Document")
    BUDAT = Column(Date, nullable=True, comment="Posting Date in the Document")
    CPUDT = Column(Date, nullable=True, comment="Day On Which Accounting Document Was Entered")
    CPUTM = Column(DateTime, nullable=True, comment="Time of Entry")
    USNAM = Column(String(12), nullable=True, comment="User Name")
    TCODE = Column(String(20), nullable=True, comment="Transaction Code")
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"), nullable=True, comment="Tax Number 1")
    WAERS = Column(String(5), nullable=True, comment="Currency Key")
    KURSF = Column(Float, nullable=True, comment="Exchange Rate")
    WWERT = Column(Date, nullable=True, comment="Translation date")
    XBLNR = Column(String(16), nullable=True, comment="Reference Document Number")
    BUKRS = Column(String(4), nullable=True, comment="Company Code")
    RMWWR = Column(Float, nullable=True, comment="Gross Invoice Amount in Document Currency")
    BEZNK = Column(Float, nullable=True, comment="Unplanned delivery costs")
    WMWST = Column(Float, nullable=True, comment="Tax amount in document currency")
    MWSKZ = Column(String(2), nullable=True, comment="Tax code")
    ZTERM = Column(String(4), nullable=True, comment="Terms of Payment Key")
    ZFBDT = Column(Date, nullable=True, comment="Baseline Date for Due Date Calculation")
    ZBD1T = Column(Float, nullable=True, comment="Cash discount days 1")
    ZBD2T = Column(Float, nullable=True, comment="Cash discount days 2")
    ZBD3T = Column(Float, nullable=True, comment="Cash discount days 3")
    ZBD1P = Column(Float, nullable=True, comment="Cash discount percentage 1")
    ZBD2P = Column(Float, nullable=True, comment="Cash discount percentage 2")
    DIEKZ = Column(String(1), nullable=True, comment="Service indicator")
    LANDL = Column(String(3), nullable=True, comment="Country of supplying country")
    LZBKZ = Column(String(3), nullable=True, comment="State central bank indicator")
    STCEG = Column(String(20), nullable=True, comment="VAT Registration Number")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="invoices")
    line_items = relationship("RSEG", back_populates="invoice_header",
                              foreign_keys="[RSEG.BELNR, RSEG.GJAHR]",
                              primaryjoin="and_(RBKP.BELNR == foreign(RSEG.BELNR), RBKP.GJAHR == foreign(RSEG.GJAHR))")


class RSEG(Base):
    """Document Item: Incoming Invoice"""
    __tablename__ = "rseg"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", "BUZEI", name="rseg_belnr_gjahr_buzei_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False, comment="Document Number of an Invoice Document")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BUZEI = Column(String(6), nullable=False, comment="Item List Number")
    EBELN = Column(String(10), nullable=True, comment="Purchasing Document Number")
    EBELP = Column(String(5), nullable=True, comment="Item Number of Purchasing Document")
    ZEKKN = Column(String(2), nullable=True, comment="Sequential number of account assignment")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    BWKEY = Column(String(4), nullable=True, comment="Valuation Area")
    BWTAR = Column(String(10), nullable=True, comment="Valuation Type")
    BUKRS = Column(String(4), nullable=True, comment="Company Code")
    WERKS = Column(String(4), nullable=True, comment="Plant")
    WRBTR = Column(Float, nullable=True, comment="Amount in Document Currency")
    SHKZG = Column(String(1), nullable=True, comment="Debit/Credit Indicator")
    MWSKZ = Column(String(2), nullable=True, comment="Tax on sales/purchases code")
    TXJCD = Column(String(15), nullable=True, comment="Tax Jur.")
    MENGE = Column(Float, nullable=True, comment="Quantity")
    BSTME = Column(String(3), nullable=True, comment="Purchase order unit of measure")
    BPMNG = Column(Float, nullable=True, comment="Quantity in Purchase Order Price Unit")
    BPRME = Column(String(3), nullable=True, comment="Order Price Unit (Purchasing)")
    LBKUM = Column(Float, nullable=True, comment="Total Valuated Stock")
    SALK3 = Column(Float, nullable=True, comment="Value of Total Valuated Stock")
    VPRSV = Column(String(1), nullable=True, comment="Price control indicator")
    VERPR = Column(Float, nullable=True, comment="Moving Average Price/Periodic Unit Price")
    STPRS = Column(Float, nullable=True, comment="Standard price")
    PEINH = Column(Float, nullable=True, comment="Price Unit")
    SKFBP = Column(Float, nullable=True, comment="Amount eligible for cash discount")
    KSCHL = Column(String(4), nullable=True, comment="Condition Type")
    created_at = Column(DateTime, default=func.now())

    invoice_header = relationship("RBKP", back_populates="line_items",
                                  foreign_keys=[BELNR, GJAHR],
                                  primaryjoin="and_(RSEG.BELNR == RBKP.BELNR, RSEG.GJAHR == RBKP.GJAHR)")


class BKPF(Base):
    """Accounting Document Header"""
    __tablename__ = "bkpf"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", name="bkpf_bukrs_belnr_gjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    BELNR = Column(String(10), nullable=False, comment="Accounting Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BLART = Column(String(2), nullable=True, comment="Document Type")
    BLDAT = Column(Date, nullable=True, comment="Document Date in Document")
    BUDAT = Column(Date, nullable=True, comment="Posting Date in the Document")
    MONAT = Column(Integer, nullable=True, comment="Fiscal Period")
    CPUDT = Column(Date, nullable=True, comment="Day On Which Accounting Document Was Entered")
    CPUTM = Column(DateTime, nullable=True, comment="Time of Entry")
    AEDAT = Column(Date, nullable=True, comment="Date of the Last Document Change")
    UPDDT = Column(Date, nullable=True, comment="Date of the Last Update")
    WWERT = Column(Date, nullable=True, comment="Translation date")
    USNAM = Column(String(12), nullable=True, comment="User Name")
    TCODE = Column(String(20), nullable=True, comment="Transaction Code")
    BVORG = Column(String(16), nullable=True, comment="Number of a Cross-Company Code Transaction")
    XBLNR = Column(String(16), nullable=True, comment="Reference Document Number")
    DBBLG = Column(String(10), nullable=True, comment="Recurring entry document number")
    STBLG = Column(String(10), nullable=True, comment="Reverse Document Number")
    STJAH = Column(String(4), nullable=True, comment="Reverse document fiscal year")
    BKTXT = Column(String(25), nullable=True, comment="Document Header Text")
    WAERS = Column(String(5), nullable=True, comment="Currency Key")
    KURSF = Column(Float, nullable=True, comment="Exchange Rate")
    KZWRS = Column(String(5), nullable=True, comment="Group Currency")
    created_at = Column(DateTime, default=func.now())

    line_items = relationship("BSEG", back_populates="doc_header",
                              foreign_keys="[BSEG.BUKRS, BSEG.BELNR, BSEG.GJAHR]",
                              primaryjoin="and_(BKPF.BUKRS == foreign(BSEG.BUKRS), BKPF.BELNR == foreign(BSEG.BELNR), BKPF.GJAHR == foreign(BSEG.GJAHR))")


class BSEG(Base):
    """Accounting Document Segment"""
    __tablename__ = "bseg"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", "BUZEI", name="bseg_keys_unique"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    BELNR = Column(String(10), nullable=False, comment="Accounting Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BUZEI = Column(String(3), nullable=False, comment="Line Item Number")
    BZIRK = Column(String(6), nullable=True, comment="Sales District")
    BSCHL = Column(String(2), nullable=True, comment="Posting Key")
    KOART = Column(String(1), nullable=True, comment="Account Type")
    UMSKZ = Column(String(1), nullable=True, comment="Special G/L Indicator")
    SHKZG = Column(String(1), nullable=True, comment="Debit/Credit Indicator")
    GSBER = Column(String(4), nullable=True, comment="Business Area")
    PARGB = Column(String(4), nullable=True, comment="Trading partner's business area")
    MWSKZ = Column(String(2), nullable=True, comment="Tax on sales/purchases code")
    DMBTR = Column(Float, nullable=True, comment="Amount in Local Currency")
    WRBTR = Column(Float, nullable=True, comment="Amount in Document Currency")
    MWSTS = Column(Float, nullable=True, comment="Tax amount in local currency")
    WMWST = Column(Float, nullable=True, comment="Tax amount in document currency")
    HWBAS = Column(Float, nullable=True, comment="Tax base amount in local currency")
    FWBAS = Column(Float, nullable=True, comment="Tax base amount in document currency")
    HWZUZ = Column(Float, nullable=True, comment="Provision amount in local currency")
    FWZUZ = Column(Float, nullable=True, comment="Provision amount in document currency")
    HKONT = Column(String(10), nullable=True, comment="General Ledger Account")
    KUNNR = Column(String(10), nullable=True, comment="Customer Number")
    LIFNR = Column(String(10), nullable=True, comment="Account Number of Vendor or Creditor")
    KOSTL = Column(String(10), nullable=True, comment="Cost Center")
    PROJK = Column(String(8), nullable=True, comment="WBS Element")
    AUFNR = Column(String(12), nullable=True, comment="Order Number")
    created_at = Column(DateTime, default=func.now())

    doc_header = relationship("BKPF", back_populates="line_items",
                               foreign_keys=[BUKRS, BELNR, GJAHR],
                               primaryjoin="and_(BSEG.BUKRS == BKPF.BUKRS, BSEG.BELNR == BKPF.BELNR, BSEG.GJAHR == BKPF.GJAHR)")


class MKPF(Base):
    """Header: Material Document"""
    __tablename__ = "mkpf"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", name="mkpf_mblnr_mjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False, comment="Number of Material Document")
    MJAHR = Column(String(4), nullable=False, comment="Material Document Year")
    VGART = Column(String(2), nullable=True, comment="Transaction/Event Type")
    BLART = Column(String(2), nullable=True, comment="Document Type")
    BLDAT = Column(Date, nullable=True, comment="Document Date in Document")
    BUDAT = Column(Date, nullable=True, comment="Posting Date in the Document")
    CPUDT = Column(Date, nullable=True, comment="Day On Which Accounting Document Was Entered")
    CPUTM = Column(DateTime, nullable=True, comment="Time of Entry")
    AEDAT = Column(Date, nullable=True, comment="Date of the Last Document Change")
    USNAM = Column(String(12), nullable=True, comment="User Name")
    TCODE = Column(String(20), nullable=True, comment="Transaction Code")
    XBLNR = Column(String(16), nullable=True, comment="Reference Document Number")
    BKTXT = Column(String(25), nullable=True, comment="Document Header Text")
    created_at = Column(DateTime, default=func.now())

    line_items = relationship("MSEG", back_populates="mat_doc_header",
                              foreign_keys="[MSEG.MBLNR, MSEG.MJAHR]",
                              primaryjoin="and_(MKPF.MBLNR == foreign(MSEG.MBLNR), MKPF.MJAHR == foreign(MSEG.MJAHR))")


class MSEG(Base):
    """Document Segment: Material"""
    __tablename__ = "mseg"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", "ZEILE", name="mseg_mblnr_mjahr_zeile_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False, comment="Number of Material Document")
    MJAHR = Column(String(4), nullable=False, comment="Material Document Year")
    ZEILE = Column(String(4), nullable=False, comment="Item in Material Document")
    BWART = Column(String(3), nullable=True, comment="Movement Type (Inventory Management)")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    WERKS = Column(String(4), nullable=True, comment="Plant")
    LGORT = Column(String(4), nullable=True, comment="Storage Location")
    CHARG = Column(String(10), nullable=True, comment="Batch Number")
    INSMK = Column(String(1), nullable=True, comment="Stock Type")
    ZUGIU = Column(String(1), nullable=True, comment="Posting to Stock in Quality Inspection")
    SOBKZ = Column(String(1), nullable=True, comment="Special Stock Indicator")
    LIFNR = Column(String(10), nullable=True, comment="Vendor number")
    KUNNR = Column(String(10), nullable=True, comment="Account number of customer")
    KOKRS = Column(String(4), nullable=True, comment="Controlling Area")
    KOSTL = Column(String(10), nullable=True, comment="Cost Center")
    PROJK = Column(String(8), nullable=True, comment="WBS Element")
    AUFNR = Column(String(12), nullable=True, comment="Order Number")
    ANLN1 = Column(String(12), nullable=True, comment="Main Asset Number")
    ANLN2 = Column(String(4), nullable=True, comment="Asset Subnumber")
    MENGE = Column(Float, nullable=True, comment="Quantity")
    MEINS = Column(String(3), nullable=True, comment="Unit of Measure")
    ERFMG = Column(Float, nullable=True, comment="Quantity in unit of entry")
    ERFME = Column(String(3), nullable=True, comment="Unit of entry")
    EBELN = Column(String(10), nullable=True, comment="Purchase Order Number")
    EBELP = Column(String(5), nullable=True, comment="PO Item Number")
    LFBJA = Column(String(4), nullable=True, comment="Fiscal year of a reference document")
    LFBNR = Column(String(10), nullable=True, comment="Document number of a reference document")
    LFPOS = Column(String(4), nullable=True, comment="Item of a reference document")
    SJAHR = Column(String(4), nullable=True, comment="Material document year")
    SMBLN = Column(String(10), nullable=True, comment="Number of material document")
    SMBLP = Column(String(4), nullable=True, comment="Item in material document")
    created_at = Column(DateTime, default=func.now())

    mat_doc_header = relationship("MKPF", back_populates="line_items",
                                   foreign_keys=[MBLNR, MJAHR],
                                   primaryjoin="and_(MSEG.MBLNR == MKPF.MBLNR, MSEG.MJAHR == MKPF.MJAHR)")
