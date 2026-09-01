/*M!999999\- enable the sandbox mode */ 

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `application_steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `application_steps` (
  `application_step_id` int(11) NOT NULL AUTO_INCREMENT,
  `application_id` int(11) NOT NULL,
  `step_order` int(11) NOT NULL,
  `label` varchar(255) NOT NULL,
  `state` varchar(20) NOT NULL DEFAULT 'pending' CHECK (`state` in ('pending','active','done')),
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`application_step_id`),
  KEY `application_id` (`application_id`),
  CONSTRAINT `application_steps_ibfk_1` FOREIGN KEY (`application_id`) REFERENCES `applications` (`application_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `application_steps` WRITE;
/*!40000 ALTER TABLE `application_steps` DISABLE KEYS */;
/*!40000 ALTER TABLE `application_steps` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `applications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `applications` (
  `application_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `target_type` varchar(20) NOT NULL CHECK (`target_type` in ('University','Scholarship')),
  `university_id` int(11) DEFAULT NULL,
  `scholarship_id` int(11) DEFAULT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'Started' CHECK (`status` in ('Started','Submitted','Under Review','Accepted','Rejected')),
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`application_id`),
  KEY `university_id` (`university_id`),
  KEY `scholarship_id` (`scholarship_id`),
  KEY `idx_applications_user` (`user_id`),
  CONSTRAINT `applications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `applications_ibfk_2` FOREIGN KEY (`university_id`) REFERENCES `universities` (`university_id`),
  CONSTRAINT `applications_ibfk_3` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`),
  CONSTRAINT `CONSTRAINT_1` CHECK (`target_type` = 'University' and `university_id` is not null and `scholarship_id` is null or `target_type` = 'Scholarship' and `scholarship_id` is not null and `university_id` is null)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `applications` WRITE;
/*!40000 ALTER TABLE `applications` DISABLE KEYS */;
/*!40000 ALTER TABLE `applications` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `countries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `countries` (
  `country_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`country_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `countries` WRITE;
/*!40000 ALTER TABLE `countries` DISABLE KEYS */;
INSERT INTO `countries` (`country_id`, `name`) VALUES (5,'Burundi'),
(6,'DR Congo'),
(3,'Kenya'),
(1,'Rwanda'),
(4,'Tanzania'),
(2,'Uganda');
/*!40000 ALTER TABLE `countries` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `document_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `document_types` (
  `document_type_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`document_type_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `document_types` WRITE;
/*!40000 ALTER TABLE `document_types` DISABLE KEYS */;
INSERT INTO `document_types` (`document_type_id`, `name`) VALUES (1,'Academic Transcript'),
(2,'National ID / Passport'),
(4,'Personal Statement'),
(3,'Recommendation Letter');
/*!40000 ALTER TABLE `document_types` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `mentor_bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `mentor_bookings` (
  `booking_id` int(11) NOT NULL AUTO_INCREMENT,
  `mentor_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `requested_at` datetime NOT NULL DEFAULT current_timestamp(),
  `status` varchar(20) NOT NULL DEFAULT 'Requested' CHECK (`status` in ('Requested','Confirmed','Completed','Cancelled')),
  PRIMARY KEY (`booking_id`),
  KEY `mentor_id` (`mentor_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `mentor_bookings_ibfk_1` FOREIGN KEY (`mentor_id`) REFERENCES `mentors` (`mentor_id`),
  CONSTRAINT `mentor_bookings_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `mentor_bookings` WRITE;
/*!40000 ALTER TABLE `mentor_bookings` DISABLE KEYS */;
/*!40000 ALTER TABLE `mentor_bookings` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `mentors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `mentors` (
  `mentor_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `role` varchar(255) DEFAULT NULL,
  `focus_area` varchar(255) DEFAULT NULL,
  `rate` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`mentor_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `mentors` WRITE;
/*!40000 ALTER TABLE `mentors` DISABLE KEYS */;
INSERT INTO `mentors` (`mentor_id`, `name`, `role`, `focus_area`, `rate`) VALUES (1,'Aline U.','UR Engineering Alum · Mastercard Scholar','Essay review, interview prep','Free · 20 min'),
(2,'Eric N.','CMU-Africa Student','IT & Engineering applications','Free · 20 min'),
(3,'Divine K.','AUCA Alum · SFAR recipient','SFAR & BRD loan process walkthrough','Free · 15 min'),
(4,'Grace M.','University of Nairobi Student','Regional (Kenya) applications','Free · 20 min');
/*!40000 ALTER TABLE `mentors` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `payment_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `application_id` int(11) DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `currency` varchar(10) NOT NULL DEFAULT 'USD',
  `method` varchar(20) NOT NULL CHECK (`method` in ('Card','Mobile Money')),
  `status` varchar(20) NOT NULL DEFAULT 'Pending' CHECK (`status` in ('Pending','Completed','Failed','Refunded')),
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`payment_id`),
  KEY `application_id` (`application_id`),
  KEY `idx_payments_user` (`user_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`application_id`) REFERENCES `applications` (`application_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `scholarship_required_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `scholarship_required_documents` (
  `scholarship_id` int(11) NOT NULL,
  `document_type_id` int(11) NOT NULL,
  PRIMARY KEY (`scholarship_id`,`document_type_id`),
  KEY `document_type_id` (`document_type_id`),
  CONSTRAINT `scholarship_required_documents_ibfk_1` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`) ON DELETE CASCADE,
  CONSTRAINT `scholarship_required_documents_ibfk_2` FOREIGN KEY (`document_type_id`) REFERENCES `document_types` (`document_type_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `scholarship_required_documents` WRITE;
/*!40000 ALTER TABLE `scholarship_required_documents` DISABLE KEYS */;
INSERT INTO `scholarship_required_documents` (`scholarship_id`, `document_type_id`) VALUES (1,1),
(1,2),
(2,1),
(2,2),
(3,1),
(3,2),
(3,3),
(3,4),
(4,1),
(4,2),
(4,3),
(5,1),
(5,2),
(6,1),
(6,2),
(6,4),
(7,1),
(7,2);
/*!40000 ALTER TABLE `scholarship_required_documents` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `scholarship_universities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `scholarship_universities` (
  `scholarship_id` int(11) NOT NULL,
  `university_id` int(11) NOT NULL,
  PRIMARY KEY (`scholarship_id`,`university_id`),
  KEY `university_id` (`university_id`),
  CONSTRAINT `scholarship_universities_ibfk_1` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`) ON DELETE CASCADE,
  CONSTRAINT `scholarship_universities_ibfk_2` FOREIGN KEY (`university_id`) REFERENCES `universities` (`university_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `scholarship_universities` WRITE;
/*!40000 ALTER TABLE `scholarship_universities` DISABLE KEYS */;
INSERT INTO `scholarship_universities` (`scholarship_id`, `university_id`) VALUES (1,1),
(1,3),
(1,4),
(1,5),
(1,11),
(2,3),
(2,5),
(3,1),
(3,2),
(3,6),
(3,8),
(4,6),
(4,7),
(4,10),
(4,12),
(7,1),
(7,2),
(7,3);
/*!40000 ALTER TABLE `scholarship_universities` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `scholarships`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `scholarships` (
  `scholarship_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `provider` varchar(255) DEFAULT NULL,
  `category` varchar(50) NOT NULL CHECK (`category` in ('Government','NGO','International','Local','Employer')),
  `amount` varchar(255) DEFAULT NULL,
  `deadline` varchar(255) DEFAULT NULL,
  `eligibility_notes` text DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `is_partner` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`scholarship_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `scholarships` WRITE;
/*!40000 ALTER TABLE `scholarships` DISABLE KEYS */;
INSERT INTO `scholarships` (`scholarship_id`, `name`, `provider`, `category`, `amount`, `deadline`, `eligibility_notes`, `website`, `is_partner`) VALUES (1,'SFAR Student Loans','Government of Rwanda','Government','Tuition + living stipend','Rolling, annual cycle','Any accredited Rwandan institution','https://sfar.gov.rw',1),
(2,'BRD Minuza Loan Portal','Development Bank of Rwanda','Government','Varies by program','Rolling','University of Kigali, AUCA, and partner institutions','https://minuza.brd.rw/',1),
(3,'Mastercard Foundation Scholars Program','Mastercard Foundation','NGO','Full tuition + stipend','Varies by partner university','UR, CMU-Africa, Makerere (partner institutions only)',NULL,1),
(4,'DAAD Scholarships — East Africa','DAAD (Germany)','International','Full funding + travel','Varies by program','Specific graduate programs, partner universities',NULL,0),
(5,'District Community Bursary','Local district fund (example)','Local','Partial tuition support','Set by district office','Any accredited institution, district residents',NULL,0),
(6,'Twiga Capital Future Talent Award','Twiga Capital (employer-sponsored)','Employer','Full tuition + guaranteed internship','Applications open termly','Business & IT programs, any accredited institution — includes a post-graduation internship offer',NULL,0),
(7,'Virunga Works Engineering Award','Virunga Works (employer-sponsored)','Employer','Partial tuition + job placement track','Rolling','Engineering programs at UR, CMU-Africa, University of Kigali',NULL,0);
/*!40000 ALTER TABLE `scholarships` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `student_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_profiles` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `nationality` varchar(100) DEFAULT NULL,
  `district` varchar(100) DEFAULT NULL,
  `education_level` varchar(50) DEFAULT NULL CHECK (`education_level` in ('Senior 6 / A-Level','Undergraduate','Graduate','TVET','Other')),
  `previous_school` varchar(255) DEFAULT NULL,
  `grades` varchar(255) DEFAULT NULL,
  `key_subjects` text DEFAULT NULL,
  `preferred_fields` text DEFAULT NULL,
  `preferred_countries` text DEFAULT NULL,
  `financial_need` varchar(20) DEFAULT NULL CHECK (`financial_need` in ('High','Medium','Low')),
  `test_scores` varchar(255) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`user_id`),
  CONSTRAINT `student_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `student_profiles` WRITE;
/*!40000 ALTER TABLE `student_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `student_profiles` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `universities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `universities` (
  `university_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `country_id` int(11) NOT NULL,
  `tuition` varchar(255) DEFAULT NULL,
  `programs` text DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `is_partner` tinyint(1) NOT NULL DEFAULT 0,
  `deadline` varchar(255) DEFAULT NULL,
  `living_cost` varchar(255) DEFAULT NULL,
  `partner_benefits` text DEFAULT NULL,
  PRIMARY KEY (`university_id`),
  UNIQUE KEY `name` (`name`),
  KEY `idx_universities_country` (`country_id`),
  CONSTRAINT `universities_ibfk_1` FOREIGN KEY (`country_id`) REFERENCES `countries` (`country_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `universities` WRITE;
/*!40000 ALTER TABLE `universities` DISABLE KEYS */;
INSERT INTO `universities` (`university_id`, `name`, `country_id`, `tuition`, `programs`, `website`, `is_partner`, `deadline`, `living_cost`, `partner_benefits`) VALUES (1,'University of Rwanda (UR)',1,'≈ 600,000 – 1,200,000 RWF / yr','Engineering, Medicine, Business, Education, Sciences','https://www.ur.ac.rw',1,'Rolling — intake in Sept & Jan','≈ 150,000 – 250,000 RWF / month','Priority review · Application fee waiver · Exclusive scholarship matching'),
(2,'Carnegie Mellon University Africa',1,'Contact admissions for tuition & aid','ICT, Electrical & Computer Engineering, Information Technology','https://africa.engineering.cmu.edu',1,'Jan 15 (Fall intake)','Campus housing available — contact admissions','Priority review · Mastercard Scholars pathway support'),
(3,'University of Kigali',1,'≈ 700,000 – 1,500,000 RWF / yr','Law, Business, IT, Public Health','https://www.uok.ac.rw',1,'Rolling','≈ 180,000 – 280,000 RWF / month','Priority review · BRD Minuza guidance · Fee waiver for eligible applicants'),
(4,'Mount Kenya University Rwanda',1,'≈ 650,000 – 1,300,000 RWF / yr','Business, Education, Health Sciences, Journalism','https://mku.ac.rw',0,'Rolling','≈ 150,000 – 250,000 RWF / month',NULL),
(5,'Adventist University of Central Africa (AUCA)',1,'≈ 600,000 – 1,100,000 RWF / yr','Theology, Business, Nursing, Computer Science','https://www.auca.ac.rw',1,'Rolling','≈ 140,000 – 220,000 RWF / month','Priority review · BRD Minuza guidance'),
(6,'Makerere University',2,'Varies by program — see admissions','Medicine, Engineering, Agriculture, Arts','https://www.mak.ac.ug',0,'See admissions calendar','Varies — Kampala',NULL),
(7,'Kyambogo University',2,'Varies by program — see admissions','Engineering, Education, Vocational Studies','https://kyu.ac.ug',0,'See admissions calendar','Varies — Kampala',NULL),
(8,'University of Nairobi',3,'Varies by program — see admissions','Law, Medicine, Engineering, Business','https://www.uonbi.ac.ke',0,'See admissions calendar','Varies — Nairobi',NULL),
(9,'Strathmore University',3,'Varies by program — see admissions','Business, Law, IT, Actuarial Science','https://strathmore.edu',0,'See admissions calendar','Varies — Nairobi',NULL),
(10,'University of Dar es Salaam',4,'Varies by program — see admissions','Engineering, Law, Social Sciences','https://www.udsm.ac.tz',0,'See admissions calendar','Varies — Dar es Salaam',NULL),
(11,'University of Burundi',5,'Varies by program — see admissions','Medicine, Agronomy, Law, Sciences',NULL,0,'See admissions','Varies',NULL),
(12,'University of Kinshasa',6,'Varies by program — see admissions','Medicine, Law, Engineering, Economics',NULL,0,'See admissions','Varies',NULL);
/*!40000 ALTER TABLE `universities` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `university_required_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `university_required_documents` (
  `university_id` int(11) NOT NULL,
  `document_type_id` int(11) NOT NULL,
  PRIMARY KEY (`university_id`,`document_type_id`),
  KEY `document_type_id` (`document_type_id`),
  CONSTRAINT `university_required_documents_ibfk_1` FOREIGN KEY (`university_id`) REFERENCES `universities` (`university_id`) ON DELETE CASCADE,
  CONSTRAINT `university_required_documents_ibfk_2` FOREIGN KEY (`document_type_id`) REFERENCES `document_types` (`document_type_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `university_required_documents` WRITE;
/*!40000 ALTER TABLE `university_required_documents` DISABLE KEYS */;
INSERT INTO `university_required_documents` (`university_id`, `document_type_id`) VALUES (1,1),
(1,2),
(2,1),
(2,2),
(2,3),
(3,1),
(3,2),
(4,1),
(4,2),
(5,1),
(5,2),
(6,1),
(6,2),
(6,3),
(7,1),
(7,2),
(8,1),
(8,2),
(9,1),
(9,2),
(9,3),
(10,1),
(10,2),
(11,1),
(11,2),
(12,1),
(12,2);
/*!40000 ALTER TABLE `university_required_documents` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `vault_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vault_documents` (
  `vault_document_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `document_type_id` int(11) NOT NULL,
  `is_uploaded` tinyint(1) NOT NULL DEFAULT 0,
  `uploaded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`vault_document_id`),
  UNIQUE KEY `uq_user_doc` (`user_id`,`document_type_id`),
  KEY `document_type_id` (`document_type_id`),
  KEY `idx_vault_user` (`user_id`),
  CONSTRAINT `vault_documents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `vault_documents_ibfk_2` FOREIGN KEY (`document_type_id`) REFERENCES `document_types` (`document_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `vault_documents` WRITE;
/*!40000 ALTER TABLE `vault_documents` DISABLE KEYS */;
/*!40000 ALTER TABLE `vault_documents` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

