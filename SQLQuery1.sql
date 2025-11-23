IF OBJECT_ID('dbo.Receipt_Tests', 'U') IS NOT NULL
    DROP TABLE dbo.Receipt_Tests;

IF OBJECT_ID('dbo.Receipts', 'U') IS NOT NULL
    DROP TABLE dbo.Receipts;

IF OBJECT_ID('dbo.Tests', 'U') IS NOT NULL
    DROP TABLE dbo.Tests;

IF OBJECT_ID('dbo.Patients', 'U') IS NOT NULL
    DROP TABLE dbo.Patients;
GO

-- ========================================
-- Create Patients Table (Reception Form)
-- ========================================
CREATE TABLE Patients (
    MrNo INT IDENTITY(1,1) PRIMARY KEY,   -- Auto increment MR number
    RegDate DATE NOT NULL,
    ReportingDate DATE NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Gender VARCHAR(10) NOT NULL CHECK (Gender IN ('Male','Female')),
    Age INT NOT NULL,
    Doctor VARCHAR(100) NOT NULL,
    Tests VARCHAR(MAX) NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- Create Tests Table (Lab Test Master Data)
-- ========================================
CREATE TABLE Tests (
    TestId INT IDENTITY(1,1) PRIMARY KEY,
    TestName VARCHAR(100) NOT NULL,
    Price DECIMAL(10,2) NOT NULL
);
GO

-- ========================================
-- Create Receipts Table (Billing Info)
-- ========================================
CREATE TABLE Receipts (
    ReceiptId INT IDENTITY(1,1) PRIMARY KEY,
    PatientMrNo INT NOT NULL,
    TotalAmount DECIMAL(10,2) NOT NULL,
    ReportDueTime DATETIME,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (PatientMrNo) REFERENCES Patients(MrNo)
);
GO

-- ========================================
-- Create Receipt_Tests Table (Mapping Receipt <-> Tests)
-- ========================================
CREATE TABLE Receipt_Tests (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptId INT NOT NULL,
    TestId INT NOT NULL,
    FOREIGN KEY (ReceiptId) REFERENCES Receipts(ReceiptId),
    FOREIGN KEY (TestId) REFERENCES Tests(TestId)
);
GO

