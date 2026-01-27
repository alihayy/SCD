create database Lmss
-- Drop existing tables if they exist (in correct order to handle foreign keys)
IF OBJECT_ID('dbo.Receipt_Tests', 'U') IS NOT NULL
    DROP TABLE dbo.Receipt_Tests;

IF OBJECT_ID('dbo.Receipts', 'U') IS NOT NULL
    DROP TABLE dbo.Receipts;

IF OBJECT_ID('dbo.Reports', 'U') IS NOT NULL
    DROP TABLE dbo.Reports;

IF OBJECT_ID('dbo.Tests', 'U') IS NOT NULL
    DROP TABLE dbo.Tests;

IF OBJECT_ID('dbo.Doctors', 'U') IS NOT NULL
    DROP TABLE dbo.Doctors;

IF OBJECT_ID('dbo.Patients', 'U') IS NOT NULL
    DROP TABLE dbo.Patients;

IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL
    DROP TABLE dbo.Users;

IF OBJECT_ID('dbo.Inventory', 'U') IS NOT NULL
    DROP TABLE dbo.Inventory;
GO

-- ========================================
-- Create Users Table (For Authentication)
-- ========================================
CREATE TABLE Users (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Role VARCHAR(20) NOT NULL CHECK (Role IN ('Admin', 'Receptionist', 'Technician')),
    FullName VARCHAR(100) NOT NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- Create Patients Table (Reception Form)
-- ========================================
CREATE TABLE Patients (
    MrNo INT IDENTITY(1001,1) PRIMARY KEY,   -- Starting from 1001
    RegDate DATE NOT NULL,
    ReportingDate DATE NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Gender VARCHAR(10) NOT NULL CHECK (Gender IN ('Male','Female','Other')),
    Age INT NOT NULL CHECK (Age BETWEEN 1 AND 120),
    Phone VARCHAR(15),
    Address VARCHAR(255),
    Doctor VARCHAR(100) NOT NULL,
    Tests VARCHAR(MAX) NOT NULL,
    Amount DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Status VARCHAR(20) DEFAULT 'Registered' CHECK (Status IN ('Registered', 'Sample Collected', 'Testing', 'Completed', 'Delivered')),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- Create Doctors Table (Referral Doctors)
-- ========================================
CREATE TABLE Doctors (
    DoctorId INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Specialization VARCHAR(100),
    ContactNumber VARCHAR(15),
    ConsultationFee DECIMAL(10,2) DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- Create Tests Table (Lab Test Master Data)
-- ========================================
CREATE TABLE Tests (
    TestId INT IDENTITY(1,1) PRIMARY KEY,
    TestName VARCHAR(200) NOT NULL,
    NormalRange VARCHAR(100),
    Price DECIMAL(10,2) NOT NULL CHECK (Price >= 0),
    Category VARCHAR(100),
    SampleType VARCHAR(50),
    ReportingTime VARCHAR(50),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- Create Receipts Table (Billing Info)
-- ========================================
CREATE TABLE Receipts (
    ReceiptId INT IDENTITY(1,1) PRIMARY KEY,
    PatientMrNo INT NOT NULL,
    TotalAmount DECIMAL(10,2) NOT NULL CHECK (TotalAmount >= 0),
    Discount DECIMAL(10,2) DEFAULT 0,
    NetAmount DECIMAL(10,2) NOT NULL,
    PaymentStatus VARCHAR(20) DEFAULT 'Pending' CHECK (PaymentStatus IN ('Pending', 'Paid', 'Partial')),
    ReportDueTime DATETIME,
    CreatedBy INT,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (PatientMrNo) REFERENCES Patients(MrNo)
    -- Removed FOREIGN KEY (CreatedBy) REFERENCES Users(UserId) to avoid dependency issues
);
GO

-- ========================================
-- Create Receipt_Tests Table (Mapping Receipt <-> Tests)
-- ========================================
CREATE TABLE Receipt_Tests (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptId INT NOT NULL,
    TestId INT NOT NULL,
    TestPrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ReceiptId) REFERENCES Receipts(ReceiptId) ON DELETE CASCADE,
    FOREIGN KEY (TestId) REFERENCES Tests(TestId)
);
GO

-- ========================================
-- Create Reports Table (Test Results)
-- ========================================
CREATE TABLE Reports (
    ReportId INT IDENTITY(1,1) PRIMARY KEY,
    ReceiptId INT NOT NULL,
    TestId INT NOT NULL,
    ResultValue VARCHAR(100),
    NormalRange VARCHAR(100),
    Units VARCHAR(20),
    Remarks VARCHAR(500),
    Technician VARCHAR(100),
    ApprovedBy VARCHAR(100),
    ReportDate DATETIME DEFAULT GETDATE(),
    Status VARCHAR(20) DEFAULT 'Pending' CHECK (Status IN ('Pending', 'Completed', 'Approved')),
    FOREIGN KEY (ReceiptId) REFERENCES Receipts(ReceiptId),
    FOREIGN KEY (TestId) REFERENCES Tests(TestId)
);
GO

-- ========================================
-- Create Inventory Table (Lab Supplies)
-- ========================================
CREATE TABLE Inventory (
    ItemId INT IDENTITY(1,1) PRIMARY KEY,
    ItemName VARCHAR(100) NOT NULL,
    Category VARCHAR(100),
    Quantity INT NOT NULL CHECK (Quantity >= 0),
    MinQuantity INT DEFAULT 10,
    Unit VARCHAR(20),
    Price DECIMAL(10,2),
    Supplier VARCHAR(100),
    LastRestocked DATETIME DEFAULT GETDATE(),
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- ========================================
-- INSERT SAMPLE DATA
-- ========================================

-- Insert Users
INSERT INTO Users (Username, Password, Role, FullName) VALUES
('admin', 'admin123', 'Admin', 'System Administrator'),
('reception', 'reception123', 'Receptionist', 'Reception Staff'),
('technician', 'tech123', 'Technician', 'Lab Technician');
GO

-- Insert Sample Doctors
INSERT INTO Doctors (Name, Specialization, ContactNumber, ConsultationFee) VALUES
('Dr. Ahmed Khan', 'Cardiologist', '0300-1234567', 2000.00),
('Dr. Sara Ali', 'Gynecologist', '0312-7654321', 1500.00),
('Dr. Usman Malik', 'Pediatrician', '0333-9876543', 1200.00),
('Dr. Fatima Noor', 'Dermatologist', '0345-1122334', 1000.00);
GO

-- Insert All Tests with CORRECT COLUMN NAMES
INSERT INTO Tests (TestName, NormalRange, Price, Category) VALUES
('1.7 Hydroxy Progesterone', 'After 05 Days', 4500.00, 'Hormones'),
('2.4 Hours Urinary Calcium', 'Same Day', 2000.00, 'Urine Tests'),
('2.4 Hours Urinary Creatinine', 'Same Day', 4000.00, 'Urine Tests'),
('2.4 Hours Urinary Protein Creatinine Clearance', 'DAILY', 2000.00, 'Urine Tests'),
('2.4 Hrs Urinary Potassium', 'Same Day', 1500.00, 'Urine Tests'),
('2.4 Urinary Cortisol', 'DAILY', 3500.00, 'Urine Tests'),
('2.5-HYDROXY VITAMIN D', 'after 03 day', 3500.00, 'Vitamins'),
('24 Hours Urinary Protein', 'Same Day', 2000.00, 'Urine Tests'),
('A/G Ratio', 'Same Day', 1000.00, 'Biochemistry'),
('Absolute Eosinophil Count', 'DAILY', 500.00, 'Hematology'),
('ACE', 'After 3 Days', 5900.00, 'Enzymes'),
('Acetylcholine Receptor (achr) Antibody', 'DAILY', 12500.00, 'Immunology'),
('ACTH', 'After 3 Days', 5000.00, 'Hormones'),
('Ada Level For Fluid', 'DAILY', 4000.00, 'Fluid Analysis'),
('Adenosine Deaminase (ada) (serum)', 'DAILY', 4000.00, 'Enzymes'),
('AFB Culture Report', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Culture Report (Pus)', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Culture Report (Sputum 1 st day)', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Culture Report (Sputum 2 nd day)', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Culture Report (Sputum 3 rd day)', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Culture Report (Sputum)', 'After 8 Weeks', 1600.00, 'Microbiology'),
('AFB Staining', 'Same Day', 1000.00, 'Microbiology'),
('Albumin', 'Same Day', 800.00, 'Biochemistry'),
('Aldolase', 'Same Day', 1600.00, 'Enzymes'),
('ALDOSTERONE', 'DAILY', 1600.00, 'Hormones'),
('Alkaline Phosphatase (alp)', 'Same Day', 800.00, 'Liver Function'),
('Alpha 1-anti Trypsin Level', 'DAILY', 3000.00, 'Proteins'),
('Alpha Fetoprotein (serum)', 'Same Day', 3000.00, 'Tumor Markers'),
('ALT/SGPT', 'Same Day', 500.00, 'Liver Function'),
('Ama (anti Mitochondrial Antibody)', 'DAILY', 5500.00, 'Autoimmune'),
('Amoebic by Elisa (Histolytica)', 'After 5 Days', 3000.00, 'Serology'),
('Amylase (Serum)', '4 Hours', 1000.00, 'Enzymes'),
('Amylase (Urine)', 'Daily', 1000.00, 'Urine Tests'),
('Ana Profile', 'DAILY', 8000.00, 'Autoimmune'),
('Ana Qnt', 'DAILY', 4000.00, 'Autoimmune'),
('ANCA-C', 'After 5 Days', 4500.00, 'Autoimmune'),
('ANCA-P', 'After 5 Days', 4500.00, 'Autoimmune'),
('Androgen', 'DAILY', 4000.00, 'Hormones'),
('Androstendion', 'DAILY', 4000.00, 'Hormones'),
('Animal Samples', 'DAILY', 0.00, 'Special Tests'),
('Anti Cardiolipin Antibodies (IgG)', 'Same Day', 3500.00, 'Autoimmune'),
('Anti Cardiolipin Antibodies (IgM)', 'Same Day', 3500.00, 'Autoimmune'),
('Anti CCP Antibody', 'DAILY', 3000.00, 'Autoimmune'),
('Anti Centromere Antibodies', 'DAILY', 3650.00, 'Autoimmune'),
('Anti Ds DNA Antibodies', 'After 03 days', 2000.00, 'Autoimmune'),
('Anti Endomyssal Antibodies', 'After 3 Days', 4500.00, 'Autoimmune'),
('Anti Endomysial Iga', 'DAILY', 3000.00, 'Autoimmune'),
('Anti Endomysial IgG', 'DAILY', 3000.00, 'Autoimmune'),
('Anti Gladian Antibodies IgG', 'DAILY', 3000.00, 'Autoimmune'),
('Anti Glindin Antibodies Iga', 'DAILY', 3000.00, 'Autoimmune'),
('Anti Glindin Antibody ( Iga , IgG )', 'Daily', 6000.00, 'Autoimmune'),
('Anti HCV (Elisa Method)', 'Same Day', 1500.00, 'Serology'),
('Anti HDV', 'After 5 Days', 2800.00, 'Serology'),
('Anti Hepatitis A (IgG)', 'Same Day', 2200.00, 'Serology'),
('Anti Hepatitis A (IgM)', 'Same Day', 2200.00, 'Serology'),
('Anti Lkm (liver Kidney Microsomal)', 'DAILY', 7500.00, 'Autoimmune'),
('Anti Mullerian Hormone (amh)', 'DAILY', 4500.00, 'Hormones'),
('Anti Nuclear Antibodies (ANA)', 'Same Day', 1200.00, 'Autoimmune'),
('Anti Nuclear Factor (ANF)', 'Same Day', 1200.00, 'Autoimmune'),
('Anti Phospholipase A2 Receptor Antibody', 'DAILY', 12500.00, 'Autoimmune'),
('Anti phospholipid IgG', 'Same Day', 3500.00, 'Autoimmune'),
('Anti phospholipid IgM', 'Same Day', 3500.00, 'Autoimmune'),
('Anti Rabies Antibodies', 'After 7 Days', 3000.00, 'Serology'),
('Anti Thrombin III Plasma', 'DAILY', 6000.00, 'Coagulation'),
('Anti Thyroglobulin Abs (atg)', 'DAILY', 2000.00, 'Thyroid'),
('Anti Thyroid Antibodies', 'DAILY', 3500.00, 'Thyroid'),
('Anti Thyroid Peroxidase (tpo)', 'DAILY', 4000.00, 'Thyroid'),
('APTT', 'Same Day', 1000.00, 'Coagulation'),
('APTT & PT', 'Same Day', 2000.00, 'Coagulation'),
('Ascitic Fluid Analysis', 'Same Day', 1600.00, 'Fluid Analysis'),
('Ascitic Fluid C/S', 'After 03 Days', 1600.00, 'Microbiology'),
('Ascitic Fluid for Cytology', 'Daily', 3500.00, 'Cytology'),
('ASMA (Anti Smooth Muscle Antibody)', 'After 03 Days', 3200.00, 'Autoimmune'),
('ASO Titre', 'Same Day', 1200.00, 'Serology'),
('AST (GOT)', 'Same Day', 700.00, 'Liver Function'),
('B N P', 'DAILY', 3200.00, 'Cardiac'),
('B-9', 'DAILY', 5500.00, 'Vitamins'),
('Bence Jones Protein', 'Same Day', 1200.00, 'Urine Tests'),
('Beta B-2 Microglobulin', 'DAILY', 2500.00, 'Tumor Markers'),
('Beta HCG', 'Same Day', 2000.00, 'Hormones'),
('Beta-2 Glycoprotein-1 IgG', 'DAILY', 7500.00, 'Autoimmune'),
('Beta-2 Glycoprotein-1 Igm', 'DAILY', 7500.00, 'Autoimmune'),
('Bicarbonate (hco3)', 'Same Day', 1200.00, 'Electrolytes'),
('Bile Acid (serum)', 'DAILY', 4000.00, 'Liver Function'),
('Bile Pigment (urine)', 'DAILY', 700.00, 'Urine Tests'),
('Bile Salts', 'Same Days', 2000.00, 'Urine Tests'),
('Bilirubin (Direct & Indirect)', 'Same Day', 1000.00, 'Liver Function'),
('Bilirubin Direct', 'Same Day', 500.00, 'Liver Function'),
('Bilirubin Total', 'Same Day', 500.00, 'Liver Function'),
('Bleeding Time', 'Same Days', 500.00, 'Coagulation'),
('Blood Ammonia Level', 'Same Days', 4000.00, 'Liver Function'),
('Blood Glucose (random)', 'DAILY', 500.00, 'Diabetes'),
('Blood Glucose Fasting', 'Same Day', 500.00, 'Diabetes'),
('Blood Group', 'Same Day', 500.00, 'Blood Bank'),
('Blood Lactate', 'After 5 Days', 3500.00, 'Metabolic'),
('Blood Sugar (1 Hrs ABF)', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar (1/2 Hrs ABF)', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar (2 1/2 Hrs ABF)', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar (2 Hrs ABF)', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar (3 Hrs ABF)', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar After Dinner', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar After Lunch', 'Same Days', 250.00, 'Diabetes'),
('Blood Sugar Before Dinner', 'Same Day', 250.00, 'Diabetes'),
('Blood Sugar prelunch', 'Same Days', 500.00, 'Diabetes'),
('Blood Urea Nitrogen (BUN)', 'Same Day', 1000.00, 'Renal Function'),
('Bone Marrow Biopsy', 'After 3 Days', 4000.00, 'Hematology'),
('Breast Fluid C/S', 'After 03 Days', 1600.00, 'Microbiology'),
('Breast Fluid for Cytology', 'Daily', 3500.00, 'Cytology'),
('Bronchial Washing Cytology', '3 Days', 3500.00, 'Cytology'),
('Brucella Antibody By Titre', 'Same Day', 1500.00, 'Serology'),
('Brucella Antibody Test', 'Same Day', 1000.00, 'Serology'),
('Brucella IgG', 'DAILY', 4500.00, 'Serology'),
('Brucella Igm', 'DAILY', 4500.00, 'Serology'),
('C PEPTIDE', 'Same Day', 3200.00, 'Diabetes'),
('C Reactive Protein', 'Same Day', 1800.00, 'Inflammation'),
('C3', 'Same Day', 2800.00, 'Immunology'),
('C4', 'Same Day', 2800.00, 'Immunology'),
('Ca 15-3', 'DAILY', 3500.00, 'Tumor Markers'),
('CA-125', 'Same Day', 2800.00, 'Tumor Markers'),
('CA19-9', 'DAILY', 3500.00, 'Tumor Markers'),
('Calcium', 'Same Day', 1000.00, 'Electrolytes'),
('Calcium Phosphate', 'DAILY', 0.00, 'Electrolytes'),
('Calprotectin (stool)', 'DAILY', 7000.00, 'Stool Tests'),
('Cardiac Profile', 'Same Day', 5000.00, 'Cardiac'),
('CEA Level', 'Same Day', 2500.00, 'Tumor Markers'),
('Ceruloplasmin', 'After 3 Days', 2000.00, 'Metabolic'),
('Chem 7', 'DAILY', 5000.00, 'Biochemistry'),
('Chloride', 'Same Day', 1000.00, 'Electrolytes'),
('Cholesterol', 'Same Day', 500.00, 'Lipid Profile'),
('Ck-nac', 'DAILY', 800.00, 'Cardiac'),
('CKMB', 'Same Day', 800.00, 'Cardiac'),
('CMV IgG', 'Same Day', 800.00, 'Serology'),
('CMV IgM', 'Same Day', 800.00, 'Serology'),
('Cmv Per', 'DAILY', 14000.00, 'Molecular'),
('Coagulation Profile', 'Same Day', 4500.00, 'Coagulation'),
('Consultansy Fee', 'DAILY', 2000.00, 'Consultation'),
('Coombs Test (Direct)', 'Same Day', 1500.00, 'Immunology'),
('Coombs Test (Indirect)', 'Same Day', 1500.00, 'Immunology'),
('Cortisol (AM)', 'NEXT Day', 3800.00, 'Hormones'),
('Cortisol (PM)', 'NEXT Day', 3800.00, 'Hormones'),
('Covid 19 Elisa', 'DAILY', 3000.00, 'Serology'),
('Covid 19 Per', 'DAILY', 6500.00, 'Molecular'),
('Covid 19 Per For Airline', 'DAILY', 8500.00, 'Molecular'),
('Covid 19 Screening Igg Igm', 'DAILY', 3000.00, 'Serology'),
('Covid-antigen', 'DAILY', 2500.00, 'Serology'),
('CP', 'Same Day', 800.00, 'Hematology'),
('CP ESR P Film', 'Same Day', 1800.00, 'Hematology'),
('Cp Prints', 'DAILY', 150.00, 'Hematology'),
('CP with ESR', 'Same Day', 1500.00, 'Hematology'),
('CP with PFilm', 'Same Day', 1500.00, 'Hematology'),
('CPK', 'Same Day', 1000.00, 'Cardiac'),
('Creatinine', 'Same Day', 500.00, 'Renal Function'),
('Creatinine Clearance', 'Same Day', 3000.00, 'Renal Function'),
('Creatinine Kinase', 'DAILY', 2500.00, 'Cardiac'),
('CSF Analysis', 'Same Day', 1600.00, 'CSF Analysis'),
('Csf For Oligoclonal Bands', 'DAILY', 3500.00, 'CSF Analysis'),
('CSF Protein', 'Same Day', 1600.00, 'CSF Analysis'),
('CSF R/E', 'Same Day', 2000.00, 'CSF Analysis'),
('CT CLOTTING TIME', 'Same Day', 200.00, 'Coagulation'),
('Ct-scan Kub', 'DAILY', 15000.00, 'Radiology'),
('Culture for Fungus', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report', 'After 72 Hours', 3000.00, 'Microbiology'),
('Culture Report (Blood)', 'After 7 Days', 1600.00, 'Microbiology'),
('Culture Report (Blue Cap)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (C S F)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Fluid)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (HVS)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Pus)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Semen)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Sputum)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Stool)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Throat Swab)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (tissue)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Urine)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Culture Report (Wound Swab)', 'After 72 Hours', 1600.00, 'Microbiology'),
('Cytology Report', '5 Days', 3500.00, 'Cytology'),
('cytomegal virus igm', 'DAILY', 1500.00, 'Serology'),
('cytomegala virus igg', 'DAILY', 1500.00, 'Serology'),
('D-Dimer', 'Same Day', 3000.00, 'Coagulation'),
('Deamidated Giladin Peptide (dgp) Antibody, Igg , IGA', 'DAILY', 7000.00, 'Autoimmune'),
('DENGUE FEVER NS - 1', 'DAILY', 2500.00, 'Serology'),
('Dengue Igg Igm', 'DAILY', 4000.00, 'Serology'),
('Detail Lft', 'DAILY', 3000.00, 'Liver Function'),
('DGP Iga Deamidated Giladin Peptide', 'DAILY', 5500.00, 'Autoimmune'),
('DGP Igg Deamidated Giladin Peptide', 'DAILY', 5500.00, 'Autoimmune'),
('DHEA SO4(Dehydro-epiandrosterone)', 'DAILY', 4000.00, 'Hormones'),
('Dht Dihydosterone', 'DAILY', 4000.00, 'Hormones'),
('DLC', 'Same Day', 800.00, 'Hematology'),
('Drugs Screen Profile', 'DAILY', 8000.00, 'Toxicology'),
('ECG', 'Same Day', 1500.00, 'Cardiac'),
('Echinococcus Antibodies', 'After 5 Days', 5000.00, 'Serology'),
('Echo', 'DAILY', 4500.00, 'Cardiac'),
('Eeg', 'DAILY', 6600.00, 'Neurology'),
('EGFR', 'DAILY', 2500.00, 'Renal Function'),
('Elastase', 'DAILY', 3000.00, 'Pancreatic'),
('Electrolytes (na K+)', 'Same Day', 2000.00, 'Electrolytes'),
('Ena Profile', 'DAILY', 8000.00, 'Autoimmune'),
('Eosinophil Count', 'Same Day', 800.00, 'Hematology'),
('Erythropoietin (epo)', 'DAILY', 10000.00, 'Hematology'),
('ESR', 'Same Day', 500.00, 'Hematology'),
('Estradiol', 'Same Day', 4000.00, 'Hormones'),
('Estrogen', 'Same Day', 4000.00, 'Hormones'),
('Factor II Level', 'DAILY', 6000.00, 'Coagulation'),
('Factor V', 'DAILY', 6000.00, 'Coagulation'),
('FDPs', 'Same Day', 2500.00, 'Coagulation'),
('Ferritin', 'Same Day', 2500.00, 'Iron Studies'),
('Fine Needle Aspiration(FNA) Cytology', '5 Days', 7000.00, 'Cytology'),
('Fluid R/E', 'Same Day', 2000.00, 'Fluid Analysis'),
('Folic Acid (Folate Level)', 'After 3 Days', 2500.00, 'Vitamins'),
('Free T3', 'Same Day', 1800.00, 'Thyroid'),
('Free T4', 'Same Day', 1800.00, 'Thyroid'),
('Free Testosterone', 'DAILY', 8000.00, 'Hormones'),
('FSH', 'Same Day', 2000.00, 'Hormones'),
('Fungal Hyphae Smear', 'DAILY', 3000.00, 'Microbiology'),
('Fungal Staining', '24 Hours', 350.00, 'Microbiology'),
('G6pd Test', 'Same Day', 4800.00, 'Hematology'),
('Gad - 65 Antibodies', 'DAILY', 14000.00, 'Autoimmune'),
('Gamma GT', 'Same Day', 1000.00, 'Liver Function'),
('Gastrin Level', 'DAILY', 6500.00, 'Gastrointestinal'),
('Gene Expert For T.b', 'DAILY', 8000.00, 'Molecular'),
('Globulins', 'Same Day', 1000.00, 'Proteins'),
('Glycosylated Hb (HbA1C)', 'Same Day', 2200.00, 'Diabetes'),
('Gram Stain', 'Same Day', 800.00, 'Microbiology'),
('Growth Hormone', 'After 3 Days', 4000.00, 'Hormones'),
('H Pylori Antibody by ELISA', 'Same Day', 2000.00, 'Gastrointestinal'),
('H Pylori Antibody by Secreening', 'Same Day', 750.00, 'Gastrointestinal'),
('H Pylori Antigen Stool', '24 Hours', 4000.00, 'Gastrointestinal'),
('H Pylori IgG', 'DAILY', 1800.00, 'Gastrointestinal'),
('H Pylori IgM', 'DAILY', 1800.00, 'Gastrointestinal'),
('H.Pylori Screening', 'DAILY', 800.00, 'Gastrointestinal'),
('Haemoglobin', 'Same Day', 800.00, 'Hematology'),
('Hb Electrophoresis', 'Next Day', 3500.00, 'Hematology'),
('Hba1c (25 ) Test', 'DAILY', 0.00, 'Diabetes'),
('HBcAb Total', 'daily', 2500.00, 'Serology'),
('HBe Ab', 'Same Day', 2500.00, 'Serology'),
('HBeAg', 'Same Day', 2500.00, 'Serology'),
('HBsAg By ELISA', 'Same Day', 1500.00, 'Serology'),
('HBsAg By Screening Method', 'Same Day', 1200.00, 'Serology'),
('HCV Antibody', 'Same Day', 1200.00, 'Serology'),
('HCV By Screening Method', 'Same Day', 1200.00, 'Serology'),
('HDL Cholesterol', 'Same Day', 300.00, 'Lipid Profile'),
('HDV PCR Qualitative', '05 days', 6000.00, 'Molecular'),
('Hdv Per Quantitative', 'DAILY', 12000.00, 'Molecular'),
('Hep B Core IgG Antibody', 'DAILY', 2500.00, 'Serology'),
('Hep B Core Igm Antibody', 'Same Day', 2500.00, 'Serology'),
('Hep B Surface Antibody', 'Same Day', 3500.00, 'Serology'),
('Hepatitis B Profile', 'Same Day', 6000.00, 'Serology'),
('Hepatitis B Virus DNA by PCR Quantitative', 'After 7 Days', 8000.00, 'Molecular'),
('Hepatitis C virus Genotype', 'After 10 Days', 10000.00, 'Molecular'),
('Hepatitis C virus RNA PCR (Qualitative)', 'After 7 Days', 4000.00, 'Molecular'),
('Hepatitis C virus RNA PCR (Quantitative)', 'After 7 Days', 8000.00, 'Molecular'),
('Hepatitis E IgG Antibodies', 'After 3 Days', 2200.00, 'Serology'),
('Hepatitis E IgM Antibodies', 'Same Day', 2200.00, 'Serology'),
('Hepatitis B Virus DNA By PCR QUALITATIVE', 'After 7 Days', 4000.00, 'Molecular'),
('Herpes IgG', 'DAILY', 1000.00, 'Serology'),
('Herpes Igm', 'DAILY', 1000.00, 'Serology'),
('HEV ab IgG', 'DAILY', 1000.00, 'Serology'),
('Histopathology (afip)', 'DAILY', 8000.00, 'Histopathology'),
('Histopathology (Appendix)', 'After 7 Days', 4000.00, 'Histopathology'),
('Histopathology (Endometrial Currettings)', 'after 07 days', 8000.00, 'Histopathology'),
('Histopathology (Gall Bladder)', 'After 7 Days', 8000.00, 'Histopathology'),
('Histopathology (Kidney)', 'After 7 Days', 8000.00, 'Histopathology'),
('Histopathology (Liver Biopsy)', 'After 7 Days', 8000.00, 'Histopathology'),
('Histopathology (Prostate)', 'After 7 Days', 4000.00, 'Histopathology'),
('Histopathology (Right Breast)', 'After 7 Days', 3500.00, 'Histopathology'),
('Histopathology (Uterus)', 'After 7 Days', 8000.00, 'Histopathology'),
('Histopathology Er Pr Her', 'DAILY', 5000.00, 'Histopathology'),
('Histopathology Extra Large', 'DAILY', 12000.00, 'Histopathology'),
('Histopathology Large', 'After 7 Days', 8000.00, 'Histopathology'),
('Histopathology Small', 'After 7 Days', 4000.00, 'Histopathology'),
('HIV (AIDS) by ELISA', 'Same Day', 4000.00, 'Serology'),
('HIV (AIDS) By Screening', 'Same Day', 1000.00, 'Serology'),
('Hiv Per', 'DAILY', 18000.00, 'Molecular'),
('Hla B27', 'DAILY', 14000.00, 'Immunology'),
('Hla Class 1 / 2', 'DAILY', 25000.00, 'Immunology'),
('Homocystine in Blood', 'Same Day', 2000.00, 'Cardiac'),
('Hormonal Assay', 'DAILY', 6500.00, 'Hormones'),
('Hret Chest', 'DAILY', 9500.00, 'Radiology'),
('Hsv IgG', 'DAILY', 1500.00, 'Serology'),
('Hyadated Cyst by elisa', 'DAILY', 4000.00, 'Serology'),
('Hydatid (cyst)', 'DAILY', 4000.00, 'Serology'),
('ICT Malaria Test', 'Same Day', 500.00, 'Parasitology'),
('Immunoglobulin A (IgA)', 'Same Day', 3000.00, 'Immunology'),
('Immunoglobulin E (IgE)', 'Same Day', 2000.00, 'Immunology'),
('Immunoglobulin G (IgG)', 'Same Day', 2000.00, 'Immunology'),
('Immunoglobulin M (IgM)', 'Same Day', 2000.00, 'Immunology'),
('Immunoglobulins (iga,ige,igg,igm)', 'DAILY', 9000.00, 'Immunology'),
('INR PT', 'Same Day', 1000.00, 'Coagulation'),
('Insulin Growth Factor-1 (igf-1)', 'DAILY', 7500.00, 'Hormones'),
('Insulin Levels', 'Next Day', 4000.00, 'Diabetes'),
('Intact Parathyroid Hormone (IPTH)', 'After 5 Days', 3000.00, 'Hormones'),
('Interleukin 6', 'DAILY', 5000.00, 'Immunology'),
('Ionized Calcium', 'DAILY', 1500.00, 'Electrolytes'),
('Iron', 'Same Day', 1500.00, 'Iron Studies'),
('Ketones', 'Same Day', 1200.00, 'Metabolic'),
('Ketones (urine)', 'DAILY', 1600.00, 'Urine Tests'),
('L H', 'Same Day', 2000.00, 'Hormones'),
('Lactate', 'After 5 Days', 4000.00, 'Metabolic'),
('LDH', 'Same Day', 500.00, 'Enzymes'),
('LDL-Cholesterol', 'Same Day', 500.00, 'Lipid Profile'),
('Leishmaniasis Antibody', 'DAILY', 2000.00, 'Serology'),
('Lipase', 'Same Day', 1250.00, 'Pancreatic'),
('Lipid Profile', 'Same Day', 2000.00, 'Lipid Profile'),
('Lithium', 'Same Day', 1600.00, 'Toxicology'),
('Liver Function Tests', 'Same Day', 2500.00, 'Liver Function'),
('Lupus Anticoagulant', 'Same Day', 6000.00, 'Autoimmune'),
('Magnesium', 'Same Day', 1000.00, 'Electrolytes'),
('Malarial Parasite Smear (M.P)', 'Same Day', 1500.00, 'Parasitology'),
('Manual Platelet Count', 'Same Day', 800.00, 'Hematology'),
('Metanephrine (24 Hrs Urine)', 'DAILY', 4500.00, 'Hormones'),
('MrI BRAIN', 'DAILY', 18000.00, 'Radiology'),
('Myco TB DNA By PCR', 'After 07 days', 4000.00, 'Molecular'),
('Mycodot (tb) Screening', 'DAILY', 1000.00, 'Serology'),
('Mycodot (TB)Elisa', 'Same Day', 1500.00, 'Serology'),
('Ogtt', 'DAILY', 2000.00, 'Diabetes'),
('Osmality Fragility Test', 'DAILY', 3500.00, 'Hematology'),
('Osmolality (serum)', 'DAILY', 1800.00, 'Electrolytes'),
('Osmolality (spot Urine)', 'DAILY', 1800.00, 'Urine Tests'),
('Osmolality Test SODIUM', 'Same Day', 2300.00, 'Electrolytes'),
('PAP Smear', 'After 07 days', 2500.00, 'Cytology'),
('Por For Thalassemia', 'DAILY', 17000.00, 'Molecular'),
('Pericardial Fluid for Cytology', 'Daily', 3500.00, 'Cytology'),
('Phosphate (24 Hrs Urine)', 'DAILY', 1500.00, 'Urine Tests'),
('Phosphorous', 'Same Day', 1000.00, 'Electrolytes'),
('Physiotherapy Session', 'DAILY', 3000.00, 'Physiotherapy'),
('Pleural Fluid Analysis', 'Same Day', 2000.00, 'Fluid Analysis'),
('Pleural Fluid C/S', 'Daily', 1600.00, 'Microbiology'),
('Pleural Fluid For Ada Level', 'DAILY', 4000.00, 'Fluid Analysis'),
('Pleural Fluid for Cytology', 'Daily', 3500.00, 'Cytology'),
('Potassium', 'Same Day', 1000.00, 'Electrolytes'),
('PRE-Medical', 'DAILY', 15000.00, 'Package'),
('Pregnancy Test in Urine', 'Same Day', 500.00, 'Pregnancy'),
('Probnp (n-t) II', 'DAILY', 4500.00, 'Cardiac'),
('Procalcitonin (pct) (serum)', 'DAILY', 7000.00, 'Inflammation'),
('Progesterone', 'Same Day', 3000.00, 'Hormones'),
('Prolactin', 'Same Day', 2000.00, 'Hormones'),
('Protein C', 'After 15 Days', 6200.00, 'Coagulation'),
('Protein Creatinine Ratio', 'Same Day', 2000.00, 'Urine Tests'),
('Protein Electrophoresis', 'After 3 Days', 5400.00, 'Proteins'),
('Protein S', 'DAILY', 6200.00, 'Coagulation'),
('Protein Total', 'Same Day', 800.00, 'Proteins'),
('PSA (Prostatic Specific Ag)', 'Same Day', 3000.00, 'Tumor Markers'),
('PT', 'Same Day', 1000.00, 'Coagulation'),
('Pus R/E', 'Same Day', 2000.00, 'Microbiology'),
('Rabies Antibody', 'DAILY', 3500.00, 'Serology'),
('Rbc Folate', 'DAILY', 4500.00, 'Vitamins'),
('Red Cell Count', 'Same Day', 400.00, 'Hematology'),
('Red Cell Morphology', 'Same Day', 600.00, 'Hematology'),
('Reticulocyte Count', 'Same Day', 350.00, 'Hematology'),
('RFT Renal Function Tests', 'Same Day', 2000.00, 'Renal Function'),
('Rh Antibody Titre', 'Same Day', 1500.00, 'Blood Bank'),
('Rheumatoid Factor (R.A Factor)', 'Same Day', 1500.00, 'Autoimmune'),
('Rubella (IgG Antibody)', 'Same Day', 2000.00, 'Serology'),
('Rubella (IgM Antibody)', 'Same Day', 2000.00, 'Serology'),
('Semen Analysis', 'Same Day', 2500.00, 'Semen Analysis'),
('Serum Anti-gbm', 'DAILY', 8500.00, 'Autoimmune'),
('Serum Bile Acid', 'DAILY', 4000.00, 'Liver Function'),
('Serum Ceruloplasmin', 'After 3 Days', 2000.00, 'Metabolic'),
('Serum Human IgG 4', 'DAILY', 9500.00, 'Immunology'),
('Serum Pivka - II Level', 'DAILY', 4000.00, 'Liver Function'),
('Serum Valproic Acid', 'DAILY', 3200.00, 'Toxicology'),
('Sodium', 'Same Day', 1000.00, 'Electrolytes'),
('Sputum For AFB', 'Same Day', 350.00, 'Microbiology'),
('Stone Analysis', 'After 3 Days', 2500.00, 'Stone Analysis'),
('Stool For Afb', 'DAILY', 1000.00, 'Microbiology'),
('Stool For Clostridium-difficile Toxin', 'DAILY', 6500.00, 'Microbiology'),
('Stool For Fat Globulins', 'DAILY', 2000.00, 'Stool Tests'),
('Stool For Occult Blood', 'Same Day', 1000.00, 'Stool Tests'),
('Stool for Reducing Sub-pH', 'Same Day', 1000.00, 'Stool Tests'),
('Stool For Reducing Substances', 'Same Day', 400.00, 'Stool Tests'),
('Stool R/E', 'Same Day', 2000.00, 'Stool Tests'),
('Synovial Fluid R/E', 'Same Day', 2000.00, 'Fluid Analysis'),
('Syphilis (rpr)', 'DAILY', 1000.00, 'Serology'),
('T I B C (Total Iron Binding Capacity)', 'Same Day', 1500.00, 'Iron Studies'),
('T-spot For T.b', 'DAILY', 12000.00, 'Immunology'),
('T.b Elisa IgG', 'DAILY', 1000.00, 'Serology'),
('T.b Elisa Igm', 'DAILY', 1000.00, 'Serology'),
('T3 Total', 'Same Day', 1200.00, 'Thyroid'),
('T4 Total', 'Same Day', 1200.00, 'Thyroid'),
('Tb Gold Quantferon', 'DAILY', 8000.00, 'Immunology'),
('TB ICT', 'Same Day', 1000.00, 'Serology'),
('Testosterone', 'Same Day', 3000.00, 'Hormones'),
('TFT Thyroid Function Test', 'Same Day', 3000.00, 'Thyroid'),
('TLC', 'Same Day', 300.00, 'Hematology'),
('Torch Profile (IgG)', 'Same Day', 3000.00, 'Serology'),
('Torch Profile (IgM)', 'Same Day', 3000.00, 'Serology'),
('TORCH PROFILE SCREENING IgG', 'DAILY', 1500.00, 'Serology'),
('TORCH PROFILE SCREENING IgM', 'DAILY', 1500.00, 'Serology'),
('Toxoplasma (IgG Antibody)', 'Same Day', 1500.00, 'Serology'),
('Toxoplasma (IgM Antibody)', 'Same Day', 1500.00, 'Serology'),
('TPHA(Treponema Pallidum Haemagglutination)', 'Same Day', 2500.00, 'Serology'),
('Tr', 'DAILY', 1600.00, 'Thyroid'),
('Transferrin Test', 'DAILY', 1500.00, 'Iron Studies'),
('Transglutaminase Antibodies (IgG,IgA)', 'After 4 Days', 8000.00, 'Autoimmune'),
('Triglycerides', 'Same Day', 800.00, 'Lipid Profile'),
('Troponine-I', 'Same Day', 2200.00, 'Cardiac'),
('Troponine-T', 'Same Day', 2800.00, 'Cardiac'),
('TSH', 'Same Day', 1200.00, 'Thyroid'),
('Ttg Iga Transglutaminase Ab', 'DAILY', 4000.00, 'Autoimmune'),
('Ttg Igg Transglutaminase Ab', 'DAILY', 4000.00, 'Autoimmune'),
('Typhidot', 'Same Day', 1500.00, 'Serology'),
('Typhidot Elisa', 'DAILY', 2500.00, 'Serology'),
('Ultra Sound', 'DAILY', 3500.00, 'Radiology'),
('Ultrasound TVS', 'DAILY', 3000.00, 'Radiology'),
('Urea', 'Same Day', 500.00, 'Renal Function'),
('Uric Acid', 'Same Day', 700.00, 'Renal Function'),
('Urinary Albumin Creatinine Ratio', 'DAILY', 1000.00, 'Urine Tests'),
('Urinary Cortisol (Spot)', 'Same Day', 2500.00, 'Urine Tests'),
('Urinary Creatinine (Spot)', 'Same Day', 350.00, 'Urine Tests'),
('Urinary LDH (Spot)', 'Same Day', 600.00, 'Urine Tests'),
('Urinary Microalbumin (Spot)', 'Same Day', 1000.00, 'Urine Tests'),
('Urinary pH (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Potasium', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Potassium (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Protein (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Protein Creatinine Ratio', 'Same Day', 1000.00, 'Urine Tests'),
('Urinary Protein-Total (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Sodium (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Urea (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urinary Uric Acid (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urine Amylase (Spot)', 'Same Day', 500.00, 'Urine Tests'),
('Urine for Albumin', 'Same Day', 350.00, 'Urine Tests'),
('Urine for Ketones', 'Same Day', 500.00, 'Urine Tests'),
('Urine for Microalbumin', 'Same Day', 1000.00, 'Urine Tests'),
('Urine For Osmolality', 'Same Day', 800.00, 'Urine Tests'),
('Urine for pH', 'Same Day', 200.00, 'Urine Tests'),
('Urine for Protein By Strip', 'Same Day', 200.00, 'Urine Tests'),
('Urine for Reducing Substance', 'DAILY', 350.00, 'Urine Tests'),
('Urine for Reducing Substances', 'Same Day', 350.00, 'Urine Tests'),
('Urine for Sp. Gravity', 'Same Day', 200.00, 'Urine Tests'),
('Urine for Sugar', 'Same Day', 200.00, 'Urine Tests'),
('Urine for TLC (Ten Drugs)', 'Same Day', 5500.00, 'Toxicology'),
('Urine for V.M.A.(Vanillyl Mandelic Acid)', 'Same Day', 2200.00, 'Urine Tests'),
('Urine Protein Electrophoresis', 'DAILY', 4000.00, 'Urine Tests'),
('Urine R/E', 'Same Day', 500.00, 'Urine Tests'),
('Usg Abdomen + Pelvis', 'DAILY', 4500.00, 'Radiology'),
('Usg Doppler', 'DAILY', 4500.00, 'Radiology'),
('Usg Scrotum & Kub', 'Same Day', 6000.00, 'Radiology'),
('V.D.R.L', 'Same Day', 1500.00, 'Serology'),
('V.D.R.L Elisa', 'DAILY', 2500.00, 'Serology'),
('Vit B 7', 'DAILY', 0.00, 'Vitamins'),
('Vitamin A', 'DAILY', 25000.00, 'Vitamins'),
('Vitamin B12', 'Same Day', 3500.00, 'Vitamins'),
('Vitamin E', 'DAILY', 0.00, 'Vitamins'),
('Vitamin-b2', 'DAILY', 4500.00, 'Vitamins'),
('VMA', 'DAILY', 3000.00, 'Urine Tests'),
('Water Culture', 'After 3 days', 2500.00, 'Microbiology'),
('WBC Count.', 'Same Day', 200.00, 'Hematology'),
('Widal test', 'Same Day', 1000.00, 'Serology'),
('X-ray Cervical/neck Ap/lateral', 'DAILY', 1500.00, 'Radiology'),
('X-ray Chest Pa View', 'DAILY', 900.00, 'Radiology'),
('X-ray Hip Joint Both Lateral View', 'DAILY', 1500.00, 'Radiology'),
('X-ray Knee Joint Ap/lateral', 'DAILY', 2600.00, 'Radiology'),
('X-ray Lumbar Spine Lateral View', 'DAILY', 1500.00, 'Radiology'),
('X-ray Lumbar Spine Ap View', 'DAILY', 3000.00, 'Radiology'),
('X-ray Pelvis Ap View', 'DAILY', 700.00, 'Radiology'),
('X-ray Pns - Open Mouth/ Water', 'DAILY', 1800.00, 'Radiology'),
('X-ray RIB SINGLE VIEW', 'DAILY', 2500.00, 'Radiology'),
('X-ray Shoulder Left Ap View', 'DAILY', 2500.00, 'Radiology'),
('X-ray Wrist Left Pa/lateral', 'DAILY', 1000.00, 'Radiology'),
('Zinc Level', 'DAILY', 2600.00, 'Trace Elements'),
('Zinc Level(24Hrs Urine)', 'DAILY', 2500.00, 'Urine Tests'),
('Zinc Transporter 8', 'DAILY', 0.00, 'Autoimmune'),
('Zn Staining', 'DAILY', 1500.00, 'Histopathology');
GO

-- Insert Sample Patient
INSERT INTO Patients (RegDate, ReportingDate, Name, Gender, Age, Phone, Doctor, Tests, Amount) 
VALUES ('2024-01-20', '2024-01-21', 'Aliha Tariq', 'Female', 24, '0300-1234567', 'Dr. Ahmed Khan', 'CBC, Blood Sugar Fasting', 1000.00);
GO

-- Insert Sample Receipt
INSERT INTO Receipts (PatientMrNo, TotalAmount, NetAmount, PaymentStatus, ReportDueTime)
VALUES (1001, 1000.00, 1000.00, 'Paid', DATEADD(day, 1, GETDATE()));
GO

-- Insert Receipt Tests
INSERT INTO Receipt_Tests (ReceiptId, TestId, TestPrice)
VALUES (1, 1, 800.00), (1, 2, 200.00);
GO

-- Insert Sample Inventory Items
INSERT INTO Inventory (ItemName, Category, Quantity, MinQuantity, Unit, Price, Supplier) VALUES
('Blood Collection Tubes', 'Consumables', 500, 100, 'Pieces', 50.00, 'Medi Supplies'),
('Syringes 5ml', 'Consumables', 300, 50, 'Pieces', 25.00, 'Medi Supplies'),
('Glucose Reagent', 'Chemicals', 50, 10, 'Bottles', 1200.00, 'BioLab Chemicals'),
('Urine Strips', 'Consumables', 200, 30, 'Packs', 800.00, 'Diagnostic Inc');
GO

-- ========================================
-- CREATE USEFUL INDEXES FOR PERFORMANCE
-- ========================================
CREATE INDEX IX_Patients_Name ON Patients(Name);
CREATE INDEX IX_Patients_Phone ON Patients(Phone);
CREATE INDEX IX_Patients_RegDate ON Patients(RegDate);
CREATE INDEX IX_Receipts_PatientMrNo ON Receipts(PatientMrNo);
CREATE INDEX IX_Receipts_CreatedAt ON Receipts(CreatedAt);
CREATE INDEX IX_Tests_Category ON Tests(Category);
CREATE INDEX IX_Tests_TestName ON Tests(TestName);
GO

-- ========================================
-- CREATE STORED PROCEDURES FOR COMMON OPERATIONS
-- ========================================

-- Stored Procedure: Get Patient with Receipts
CREATE PROCEDURE GetPatientWithReceipts
    @MrNo INT
AS
BEGIN
    SELECT 
        p.*,
        r.ReceiptId,
        r.TotalAmount,
        r.PaymentStatus,
        r.CreatedAt as ReceiptDate
    FROM Patients p
    LEFT JOIN Receipts r ON p.MrNo = r.PatientMrNo
    WHERE p.MrNo = @MrNo
    ORDER BY r.CreatedAt DESC;
END;
GO

-- Stored Procedure: Get Daily Revenue Summary
CREATE PROCEDURE GetDailyRevenueSummary
    @Date DATE
AS
BEGIN
    SELECT 
        COUNT(*) as TotalPatients,
        SUM(TotalAmount) as TotalRevenue,
        SUM(CASE WHEN PaymentStatus = 'Paid' THEN TotalAmount ELSE 0 END) as PaidAmount,
        SUM(CASE WHEN PaymentStatus = 'Pending' THEN TotalAmount ELSE 0 END) as PendingAmount
    FROM Receipts
    WHERE CAST(CreatedAt AS DATE) = @Date;
END;
GO

-- Stored Procedure: Get Low Stock Items
CREATE PROCEDURE GetLowStockItems
AS
BEGIN
    SELECT 
        ItemName,
        Quantity,
        MinQuantity,
        Unit,
        (Quantity - MinQuantity) as RemainingStock
    FROM Inventory
    WHERE Quantity <= MinQuantity
    ORDER BY RemainingStock ASC;
END;
GO

-- ========================================
-- CREATE VIEWS FOR REPORTING
-- ========================================

-- View: Patient Summary View
CREATE VIEW PatientSummary AS
SELECT 
    p.MrNo,
    p.Name,
    p.Gender,
    p.Age,
    p.Doctor,
    p.Tests,
    p.Amount,
    p.RegDate,
    p.Status,
    COUNT(r.ReceiptId) as TotalReceipts,
    SUM(r.TotalAmount) as TotalPaid
FROM Patients p
LEFT JOIN Receipts r ON p.MrNo = r.PatientMrNo AND r.PaymentStatus = 'Paid'
GROUP BY p.MrNo, p.Name, p.Gender, p.Age, p.Doctor, p.Tests, p.Amount, p.RegDate, p.Status;
GO

-- View: Daily Revenue View
CREATE VIEW DailyRevenue AS
SELECT 
    CAST(CreatedAt AS DATE) as RevenueDate,
    COUNT(*) as TotalReceipts,
    SUM(TotalAmount) as TotalAmount,
    SUM(NetAmount) as NetAmount,
    SUM(Discount) as TotalDiscount
FROM Receipts
GROUP BY CAST(CreatedAt AS DATE);
GO

-- View: Test Popularity View
CREATE VIEW TestPopularity AS
SELECT 
    t.TestName,
    t.Category,
    t.Price,
    COUNT(rt.TestId) as TimesOrdered,
    COUNT(rt.TestId) * t.Price as TotalRevenue
FROM Tests t
LEFT JOIN Receipt_Tests rt ON t.TestId = rt.TestId
GROUP BY t.TestId, t.TestName, t.Category, t.Price;
GO

-- ========================================
-- PRINT CONFIRMATION MESSAGE
-- ========================================
PRINT '✅ Database schema created successfully!';
PRINT '📊 Tables created: Users, Patients, Doctors, Tests, Receipts, Receipt_Tests, Reports, Inventory';
PRINT '🧪 464 tests inserted with correct rates and categories';
PRINT '👥 Sample data inserted for testing';
PRINT '⚡ Indexes and stored procedures created for performance';
PRINT '📈 Views created for reporting';
PRINT '';
PRINT '🎯 Ready to use! You can now run your lab management system.';
GO
UPDATE Users SET Password = 'Imran@4200', FullName = 'Administrator' 
WHERE Username = 'admin';

UPDATE Users SET Password = 'Rec@001', FullName = 'Reception Staff'
WHERE Username = 'reception';

UPDATE Users SET Password = 'Tech@123', FullName = 'Lab Technician'
WHERE Username = 'technician';

SELECT * FROM users;

-- Update existing users with hashed passwords
UPDATE Users SET 
    Password = 'pbkdf2:sha256:260000$XcD8hV8yQ2eT7w6R$hashed_password_here',
    FullName = 'System Administrator'
WHERE Username = 'admin' AND Role = 'Admin';

UPDATE Users SET 
    Password = 'pbkdf2:sha256:260000$Y7eT2w6RXcD8hV8y$hashed_password_here', 
    FullName = 'Reception Staff'
WHERE Username = 'reception' AND Role = 'Receptionist';

UPDATE Users SET 
    Password = 'pbkdf2:sha256:260000$Z8hV8yQ2eT7w6RXc$hashed_password_here',
    FullName = 'Lab Technician' 
WHERE Username = 'technician' AND Role = 'Technician';

-- Verify the updates
SELECT UserId, Username, Role, FullName, LEN(Password) as PasswordLength 
FROM Users;


ALTER TABLE Tests 
ADD Male_Range_Min DECIMAL(10, 2) NULL,
    Male_Range_Max DECIMAL(10, 2) NULL,
    Female_Range_Min DECIMAL(10, 2) NULL,
    Female_Range_Max DECIMAL(10, 2) NULL,
    Range_Unit VARCHAR(50) NULL,
    Interpretation_Low NVARCHAR(500) NULL,
    Interpretation_Normal NVARCHAR(500) NULL,
    Interpretation_High NVARCHAR(500) NULL,
    Sample_Type VARCHAR(100) NULL,
    Methodology VARCHAR(200) NULL,
    Turnaround_Time VARCHAR(50) NULL,
    Department VARCHAR(100) NULL;
GO

-- Rename NormalRange column if exists
IF EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
          WHERE TABLE_NAME = 'Tests' AND COLUMN_NAME = 'NormalRange')
BEGIN
    EXEC sp_rename 'Tests.NormalRange', 'Range_Text', 'COLUMN';
END
GO

PRINT '✅ Tests table structure updated successfully!';
PRINT '📊 User can now add gender-specific ranges manually through the interface';
GO


IF OBJECT_ID('PatientSummary', 'V') IS NOT NULL
    DROP VIEW PatientSummary;
GO

CREATE VIEW PatientSummary AS
SELECT 
    p.MrNo,
    p.Name,
    p.Gender,
    p.Age,
    p.Doctor,
    p.Tests,
    p.Amount,
    p.RegDate,
    p.Status,
    COUNT(r.ReceiptId) AS TotalReceipts,
    ISNULL(SUM(r.TotalAmount),0) AS TotalPaid
FROM Patients p
LEFT JOIN Receipts r ON p.MrNo = r.PatientMrNo
GROUP BY 
    p.MrNo, p.Name, p.Gender, p.Age, 
    p.Doctor, p.Tests, p.Amount, 
    p.RegDate, p.Status;
GO
SELECT * FROM sys.views WHERE name = 'PatientSummary';

SELECT Username, Password, Role FROM Users;
SELECT UserId, Username, Password, Role, IsActive
FROM Users
WHERE Username='admin';


-- UPDATE wala part - CORRECT IT
UPDATE Users SET Password = 'Imran@4200', FullName = 'System Administrator' 
WHERE Username = 'admin';

UPDATE Users SET Password = 'Rec@001', FullName = 'Reception Staff'
WHERE Username = 'reception';

UPDATE Users SET Password = 'Tech@123', FullName = 'Lab Technician'
WHERE Username = 'technician';
