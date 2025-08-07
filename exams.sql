-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: exams
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `user_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `admin_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1,1);
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `answer`
--

DROP TABLE IF EXISTS `answer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answer` (
  `question_id` int NOT NULL,
  `answer_text` varchar(100) NOT NULL,
  `is_correct` tinyint(1) NOT NULL,
  `explanation` varchar(200) DEFAULT NULL,
  `createBy` varchar(50) NOT NULL,
  `user_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `question_id` (`question_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `answer_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`),
  CONSTRAINT `answer_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=189 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `answer`
--

LOCK TABLES `answer` WRITE;
/*!40000 ALTER TABLE `answer` DISABLE KEYS */;
INSERT INTO `answer` VALUES (1,'3',0,NULL,'admin',1,1),(1,'4',1,NULL,'admin',1,2),(1,'5',0,NULL,'admin',1,3),(1,'6',0,NULL,'admin',1,4),(2,'x = ±2',1,NULL,'admin',1,5),(2,'x = ±4',0,NULL,'admin',1,6),(2,'x = 2',0,NULL,'admin',1,7),(2,'x = -2',0,NULL,'admin',1,8),(3,'v = s/t',1,NULL,'admin',1,9),(3,'v = s*t',0,NULL,'admin',1,10),(3,'v = t/s',0,NULL,'admin',1,11),(3,'v = s+t',0,NULL,'admin',1,12),(4,'9.8 m/s²',1,NULL,'admin',1,13),(4,'10 m/s²',0,NULL,'admin',1,14),(4,'9.6 m/s²',0,NULL,'admin',1,15),(4,'8 m/s²',0,NULL,'admin',1,16),(5,'H2O',1,NULL,'admin',1,17),(5,'H2O2',0,NULL,'admin',1,18),(5,'HO',0,NULL,'admin',1,19),(5,'H3O',0,NULL,'admin',1,20),(6,'x = 3',1,NULL,'admin',1,21),(6,'x = 4',0,NULL,'admin',1,22),(6,'x = 5',0,NULL,'admin',1,23),(6,'x = 2',0,NULL,'admin',1,24),(7,'4',1,NULL,'admin',1,25),(7,'8',0,NULL,'admin',1,26),(7,'16',0,NULL,'admin',1,27),(7,'2',0,NULL,'admin',1,28),(8,'8',1,NULL,'admin',1,29),(8,'6',0,NULL,'admin',1,30),(8,'9',0,NULL,'admin',1,31),(8,'12',0,NULL,'admin',1,32),(9,'25 cm²',1,NULL,'admin',1,33),(9,'20 cm²',0,NULL,'admin',1,34),(9,'10 cm²',0,NULL,'admin',1,35),(9,'15 cm²',0,NULL,'admin',1,36),(10,'44 cm',1,NULL,'admin',1,37),(10,'14 cm',0,NULL,'admin',1,38),(10,'22 cm',0,NULL,'admin',1,39),(10,'28 cm',0,NULL,'admin',1,40),(11,'27 cm³',1,NULL,'admin',1,41),(11,'9 cm³',0,NULL,'admin',1,42),(11,'18 cm³',0,NULL,'admin',1,43),(11,'36 cm³',0,NULL,'admin',1,44),(12,'2x',1,NULL,'admin',1,45),(12,'x²',0,NULL,'admin',1,46),(12,'x',0,NULL,'admin',1,47),(12,'2x²',0,NULL,'admin',1,48),(13,'x²/2 + C',1,NULL,'admin',1,49),(13,'x² + C',0,NULL,'admin',1,50),(13,'2x + C',0,NULL,'admin',1,51),(13,'x + C',0,NULL,'admin',1,52),(14,'Quán tính',1,NULL,'admin',1,53),(14,'Gia tốc',0,NULL,'admin',1,54),(14,'Tác dụng phản tác dụng',0,NULL,'admin',1,55),(14,'Hấp dẫn',0,NULL,'admin',1,56),(15,'p = mv',1,NULL,'admin',1,57),(15,'p = ma',0,NULL,'admin',1,58),(15,'p = Ft',0,NULL,'admin',1,59),(15,'p = mv²',0,NULL,'admin',1,60),(16,'100°C',1,NULL,'admin',1,61),(16,'0°C',0,NULL,'admin',1,62),(16,'50°C',0,NULL,'admin',1,63),(16,'200°C',0,NULL,'admin',1,64),(17,'Oát (W)',1,NULL,'admin',1,65),(17,'Gam (g)',0,NULL,'admin',1,66),(17,'Giây (s)',0,NULL,'admin',1,67),(17,'Jun (J)',0,NULL,'admin',1,68),(18,'V= R/I',0,NULL,'admin',1,69),(18,'R = V.I',0,NULL,'admin',1,70),(18,'I = R/V',0,NULL,'admin',1,71),(18,'V = I.R',1,NULL,'admin',1,72),(19,'Cường độ dòng điện chạy qua dây.',0,NULL,'admin',1,73),(19,'Hiệu điện thế giữa hai đầu dây.',0,NULL,'admin',1,74),(19,'Vật liệu, chiều dài và tiết diện của dây.',1,NULL,'admin',1,75),(19,'Thời gian dòng điện chạy qua dây.',0,NULL,'admin',1,76),(20,'0',0,NULL,'admin',1,77),(20,'+1',1,NULL,'admin',1,78),(20,'-1',0,NULL,'admin',1,79),(20,'+2',0,NULL,'admin',1,80),(21,'HCl',1,NULL,'admin',1,81),(21,'H₂CO₃',0,NULL,'admin',1,82),(21,'CH₃COOH',0,NULL,'admin',1,83),(21,'H₂S',0,NULL,'admin',1,84),(22,'CH₄',1,NULL,'admin',1,85),(22,'C₂H₆',0,NULL,'admin',1,86),(22,'C₂H₄',0,NULL,'admin',1,87),(22,'C₃H₈',0,NULL,'admin',1,88),(23,'C₂H₆O',1,NULL,'admin',1,89),(23,'C₂H₄O₂',0,NULL,'admin',1,90),(23,'C₂H₆',0,NULL,'admin',1,91),(23,'CH₃OH',0,NULL,'admin',1,92),(24,'go',0,NULL,'admin',1,93),(24,'gone',0,NULL,'admin',1,94),(24,'went',1,NULL,'admin',1,95),(24,'going',0,NULL,'admin',1,96),(25,'speak',0,NULL,'admin',1,97),(25,'speaks',1,NULL,'admin',1,98),(25,'speaking',0,NULL,'admin',1,99),(25,'spoken',0,NULL,'admin',1,100),(26,'Ugly',0,NULL,'admin',1,101),(26,'Pretty',1,NULL,'admin',1,102),(26,'Dirty',0,NULL,'admin',1,103),(26,'Bad',0,NULL,'admin',1,104),(27,'Large',0,NULL,'admin',1,105),(27,'Huge',0,NULL,'admin',1,106),(27,'Tiny',1,NULL,'admin',1,107),(27,'Tall',0,NULL,'admin',1,108),(28,'is sleeping',0,NULL,'admin',1,109),(28,'The cat',1,NULL,'admin',1,110),(28,'sleeping',0,NULL,'admin',1,111),(28,'is',0,NULL,'admin',1,112),(29,'Past Simple',0,NULL,'admin',1,113),(29,'Present Simple',0,NULL,'admin',1,114),(29,'Present Continuous',1,NULL,'admin',1,115),(29,'Future Simple',0,NULL,'admin',1,116),(30,'Thế kỷ VII trước Công nguyên',1,NULL,'admin',1,117),(30,'Thế kỷ III trước Công nguyên',0,NULL,'admin',1,118),(30,'Năm 1000 sau Công nguyên',0,NULL,'admin',1,119),(30,'Thế kỷ I sau Công nguyên',0,NULL,'admin',1,120),(31,'An Dương Vương',1,NULL,'admin',1,121),(31,'Hùng Vương',0,NULL,'admin',1,122),(31,'Triệu Đà',0,NULL,'admin',1,123),(31,'Ngô Quyền',0,NULL,'admin',1,124),(32,'Thế kỷ XVIII',1,NULL,'admin',1,125),(32,'Thế kỷ XVII',0,NULL,'admin',1,126),(32,'Thế kỷ XIX',0,NULL,'admin',1,127),(32,'Thế kỷ XVI',0,NULL,'admin',1,128),(33,'Bảo Đại',1,NULL,'admin',1,129),(33,'Gia Long',0,NULL,'admin',1,130),(33,'Minh Mạng',0,NULL,'admin',1,131),(33,'Tự Đức',0,NULL,'admin',1,132),(34,'1945',1,NULL,'admin',1,133),(34,'1946',0,NULL,'admin',1,134),(34,'1944',0,NULL,'admin',1,135),(34,'1943',0,NULL,'admin',1,136),(35,'7 tháng 5 năm 1954',1,NULL,'admin',1,137),(35,'2 tháng 9 năm 1945',0,NULL,'admin',1,138),(35,'30 tháng 4 năm 1975',0,NULL,'admin',1,139),(35,'20 tháng 7 năm 1954',0,NULL,'admin',1,140),(36,'Fansipan',1,NULL,'admin',1,141),(36,'Phu Si Lung',0,NULL,'admin',1,142),(36,'Ngoc Linh',0,NULL,'admin',1,143),(36,'Bach Ma',0,NULL,'admin',1,144),(37,'Sông Hồng',0,NULL,'admin',1,145),(37,'Sông Đồng Nai',1,NULL,'admin',1,146),(37,'Sông Cửu Long',0,NULL,'admin',1,147),(37,'Sông Mê Kông',0,NULL,'admin',1,148),(38,'TP. Hồ Chí Minh, Bình Dương, Đồng Nai và Bà Rịa - Vũng Tàu',1,NULL,'admin',1,149),(38,'Hà Nội, Hải Phòng, Quảng Ninh và Bắc Ninh',0,NULL,'admin',1,150),(38,'Đà Nẵng, Thừa Thiên Huế, Quảng Nam và Quảng Ngãi',0,NULL,'admin',1,151),(38,'Cần Thơ, An Giang, Kiên Giang và Sóc Trăng',0,NULL,'admin',1,152),(39,'Lúa',1,NULL,'admin',1,153),(39,'Ngô',0,NULL,'admin',1,154),(39,'Cao su',0,NULL,'admin',1,155),(39,'Cà phê',0,NULL,'admin',1,156),(40,'khoảng 100 triệu',0,NULL,'admin',1,157),(40,'khoảng 100,3 triệu',0,NULL,'admin',1,158),(40,'khoảng 101,1 triệu',0,NULL,'admin',1,159),(40,'khoảng 101,6 triệu',1,NULL,'admin',1,160),(41,'Hà Nội',0,NULL,'admin',1,161),(41,'TP. Hồ Chí Minh',1,NULL,'admin',1,162),(41,'Cần Thơ',0,NULL,'admin',1,163),(41,'Hải Phòng',0,NULL,'admin',1,164),(42,'Nhân tế bào',1,NULL,'admin',1,165),(42,'Ti thể',0,NULL,'admin',1,166),(42,'Ribosome',0,NULL,'admin',1,167),(42,'Lysosome',0,NULL,'admin',1,168),(43,'Thụ tinh',0,NULL,'admin',1,169),(43,'Nguyên phân',1,NULL,'admin',1,170),(43,'Tiêu hóa',0,NULL,'admin',1,171),(43,'Trao đổi chất',0,NULL,'admin',1,172),(44,'Một loại tế bào',0,NULL,'admin',1,173),(44,'Một đoạn ADN mang thông tin di truyền',1,NULL,'admin',1,174),(44,'Một loại protein',0,NULL,'admin',1,175),(44,'Một bào quan trong tế bào',0,NULL,'admin',1,176),(45,'Chuỗi xoắn kép',1,NULL,'admin',1,177),(45,'Dạng hình cầu',0,NULL,'admin',1,178),(45,'Chuỗi xoắn đơn',0,NULL,'admin',1,179),(45,'Mạch thẳng không xoắn',0,NULL,'admin',1,180),(46,'Động vật ăn thịt',0,NULL,'admin',1,181),(46,'Sinh vật phân giải',0,NULL,'admin',1,182),(46,'Sinh vật sản xuất',1,NULL,'admin',1,183),(46,'Động vật ăn cỏ',0,NULL,'admin',1,184),(47,'Sự hấp thụ nước của thực vật',0,NULL,'admin',1,185),(47,'Sự phát triển của tầng ozone',0,NULL,'admin',1,186),(47,'Sự gia tăng khí CO₂ và các khí gây giữ nhiệt',1,NULL,'admin',1,187),(47,'Sự giảm nhiệt độ toàn cầu',0,NULL,'admin',1,188);
/*!40000 ALTER TABLE `answer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chapter`
--

DROP TABLE IF EXISTS `chapter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chapter` (
  `chapter_name` varchar(50) NOT NULL,
  `subject_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `chapter_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chapter`
--

LOCK TABLES `chapter` WRITE;
/*!40000 ALTER TABLE `chapter` DISABLE KEYS */;
INSERT INTO `chapter` VALUES ('Đại số',1,1),('Hình học',1,2),('Giải tích',1,3),('Cơ học',2,4),('Nhiệt học',2,5),('Điện học',2,6),('Hóa vô cơ',3,7),('Hóa hữu cơ',3,8),('Grammar',4,9),('Vocabulary',4,10),('Reading',4,11),('Lịch sử cổ đại',5,12),('Lịch sử cận đại',5,13),('Lịch sử hiện đại',5,14),('Địa lý tự nhiên',6,15),('Địa lý kinh tế',6,16),('Địa lý dân cư',6,17),('Tế bào học',7,18),('Di truyền học',7,19),('Sinh thái học',7,20);
/*!40000 ALTER TABLE `chapter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comment`
--

DROP TABLE IF EXISTS `comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comment` (
  `exam_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `exam_id` (`exam_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`id`),
  CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;
INSERT INTO `comment` VALUES (1,2,'Bài thi này khá thú vị, nhưng một số câu hơi khó!','2025-08-05 23:16:08','2025-08-05 23:16:08',1),(1,3,'Thời gian làm bài vừa đủ, cảm ơn admin!','2025-08-05 23:16:08','2025-08-05 23:16:08',2),(2,4,'Câu hỏi về điện học rất hay, cần thêm ví dụ thực tế.','2025-08-05 23:16:08','2025-08-05 23:16:08',3),(2,1,'Đã cập nhật một số câu hỏi dựa trên phản hồi.','2025-08-05 23:16:08','2025-08-05 23:16:08',4),(3,2,'Thời gian quá ngắn, cần tăng thêm 5 phút.','2025-08-05 23:16:08','2025-08-05 23:16:08',5),(4,3,'Rất hài lòng với độ khó của đề thi này.','2025-08-05 23:16:08','2025-08-05 23:16:08',6),(5,4,'Cần giải thích thêm về công thức động lượng.','2025-08-05 23:16:08','2025-08-05 23:16:08',7),(6,2,'Đề thi cân bằng, nhưng có lỗi typo ở câu 5.','2025-08-05 23:16:08','2025-08-05 23:16:08',8),(7,3,'Phần từ vựng hơi khó, đề nghị giảm độ khó.','2025-08-05 23:16:08','2025-08-05 23:16:08',9),(8,4,'Rất bổ ích, mong có thêm đề tương tự!','2025-08-05 23:16:08','2025-08-05 23:16:08',10),(14,2,'test','2025-08-05 23:45:03','2025-08-05 23:15:39',11),(2,2,'câu hỏi ít vậy bro','2025-08-06 00:04:01','2025-08-05 23:55:31',12),(2,2,'thêm câu hỏi thì sẽ tốt hơn á bro\r\nthử xem đi bro\r\nalo','2025-08-06 00:04:18','2025-08-05 23:55:31',13),(2,2,'Đầu tiên, chúng tôi sẽ biến vài đặc trưng có kiểu dữ liệu số thực (float64) thành kiểu dữ liệu số nguyên (int64) để thực hiện bước vẽ biểu đồ Boxplot trực quan các đặc trưng có giá trị ngoại lai. Các đặc trưng cần biến đổi bao gồm study-hours-per-day, social-media-hours, netflix-hours, attendance-percentage, sleep-hours, mental-health-rating, previous-gpa, stress-level, screen-time, time-management-score.','2025-08-06 00:05:02','2025-08-05 23:55:31',14),(2,2,'Bạn có thể thử đoạn này trong Overleaf và nếu vẫn gặp lỗi, gửi lại thông báo lỗi mình sẽ giúp fix ngay. Hoặc nếu bạn muốn mình thêm thẳng vào file .tex của bạn thì mình có thể làm giúp luôn.','2025-08-06 00:05:45','2025-08-05 23:55:31',15),(2,3,'? Rất hay! Đây là vấn đề thường gặp khi chèn đoạn mã có tiếng Việt có dấu vào môi trường listings hoặc tcolorbox trong LaTeX: mặc định nó không hỗ trợ Unicode nên sẽ làm mất hoặc lỗi ký tự.','2025-08-06 00:06:28','2025-08-05 23:55:31',16),(2,4,'Bạn muốn mình sửa một bảng cụ thể nào đó để thêm dòng xuống dòng cho bạn không? Gửi nội dung mình sẽ hỗ trợ ngay.','2025-08-06 00:07:03','2025-08-05 23:55:31',17),(2,4,'https://www.youtube.com/watch?v=xD8Xchuxq8g&list=RDmKxzJzp6oes&index=12','2025-08-06 00:07:23','2025-08-05 23:55:31',18),(2,4,'“Cường độ dòng điện chạy qua một dây dẫn tỉ lệ thuận với hiệu điện thế đặt vào hai đầu dây và tỉ lệ nghịch với điện trở của dây.”','2025-08-06 00:08:02','2025-08-05 23:55:31',19),(2,1,'Các bạn làm tốt lắm!','2025-08-06 00:08:42','2025-08-05 23:55:31',20);
/*!40000 ALTER TABLE `comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exam`
--

DROP TABLE IF EXISTS `exam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam` (
  `exam_name` varchar(50) NOT NULL,
  `subject_id` int NOT NULL,
  `duration` int NOT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `createBy` varchar(50) NOT NULL,
  `createAt` datetime NOT NULL,
  `user_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `subject_id` (`subject_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `exam_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`),
  CONSTRAINT `exam_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exam`
--

LOCK TABLES `exam` WRITE;
/*!40000 ALTER TABLE `exam` DISABLE KEYS */;
INSERT INTO `exam` VALUES ('Kiểm tra Toán học giữa kỳ',1,10,'2025-08-06 23:16:08','2025-08-07 00:46:08','admin','2025-08-05 23:16:08',1,1),('Kiểm tra Vật lý cuối kỳ',2,5,'2025-08-12 23:16:08','2025-08-13 01:16:08','admin','2025-08-05 23:16:08',1,2),('Kiểm tra Hóa học 15 phút',3,5,'2025-08-08 23:16:08','2025-08-08 23:31:08','admin','2025-08-05 23:16:08',1,3),('Kiểm tra Toán học tổng hợp',1,120,'2025-08-07 23:16:08','2025-08-08 01:16:08','admin','2025-08-05 23:16:08',1,4),('Kiểm tra Vật lý cơ bản',2,90,'2025-08-09 23:16:08','2025-08-10 00:46:08','admin','2025-08-05 23:16:08',1,5),('Kiểm tra Hóa học tổng hợp',3,75,'2025-08-10 23:16:08','2025-08-11 00:31:08','admin','2025-08-05 23:16:08',1,6),('English Basic Test',4,60,'2025-08-11 23:16:08','2025-08-12 00:16:08','admin','2025-08-05 23:16:08',1,7),('Kiểm tra Lịch sử Việt Nam',5,45,'2025-08-13 23:16:08','2025-08-14 00:01:08','admin','2025-08-05 23:16:08',1,8),('Kiểm tra Địa lý Việt Nam',6,60,'2025-08-14 23:16:08','2025-08-15 00:16:08','admin','2025-08-05 23:16:08',1,9),('Kiểm tra Sinh học cơ bản',7,90,'2025-08-15 23:16:08','2025-08-16 00:46:08','admin','2025-08-05 23:16:08',1,10),('Kiểm tra Toán học nâng cao',1,150,'2025-08-17 23:16:08','2025-08-18 01:46:08','admin','2025-08-05 23:16:08',1,11),('Kiểm tra Vật lý nâng cao',2,180,'2025-08-19 23:16:08','2025-08-20 02:16:08','admin','2025-08-05 23:16:08',1,12),('Kiểm tra tổng hợp đa môn',1,120,'2025-08-20 23:16:08','2025-08-21 01:16:08','admin','2025-08-05 23:16:08',1,13),('Test ngẫu nhiên',1,6,NULL,NULL,'Nguyễn Văn A','2025-08-05 23:43:43',2,14);
/*!40000 ALTER TABLE `exam` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exam_questions`
--

DROP TABLE IF EXISTS `exam_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_questions` (
  `exam_id` int NOT NULL,
  `question_id` int NOT NULL,
  `number_of_questions` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `exam_id` (`exam_id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `exam_questions_ibfk_1` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`id`),
  CONSTRAINT `exam_questions_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exam_questions`
--

LOCK TABLES `exam_questions` WRITE;
/*!40000 ALTER TABLE `exam_questions` DISABLE KEYS */;
INSERT INTO `exam_questions` VALUES (1,1,1,1),(1,2,2,2),(2,3,1,3),(2,4,2,4),(3,5,1,5),(4,1,1,6),(4,2,2,7),(4,6,3,8),(4,7,4,9),(4,8,5,10),(4,9,6,11),(4,10,7,12),(4,11,8,13),(4,12,9,14),(4,13,10,15),(5,3,1,16),(5,4,2,17),(5,14,3,18),(5,15,4,19),(5,16,5,20),(5,17,6,21),(5,18,7,22),(5,19,8,23),(5,20,9,24),(5,21,10,25),(6,5,1,26),(6,20,2,27),(6,21,3,28),(6,22,4,29),(6,23,5,30),(6,1,6,31),(6,2,7,32),(6,3,8,33),(6,4,9,34),(6,6,10,35),(7,24,1,36),(7,25,2,37),(7,26,3,38),(7,27,4,39),(7,28,5,40),(7,29,6,41),(7,1,7,42),(7,2,8,43),(7,3,9,44),(7,4,10,45),(8,30,1,46),(8,31,2,47),(8,32,3,48),(8,33,4,49),(8,34,5,50),(8,1,6,51),(8,2,7,52),(8,3,8,53),(8,4,9,54),(8,5,10,55),(9,35,1,56),(9,36,2,57),(9,37,3,58),(9,38,4,59),(9,39,5,60),(9,40,6,61),(9,6,7,62),(9,7,8,63),(9,8,9,64),(9,9,10,65),(10,41,1,66),(10,42,2,67),(10,43,3,68),(10,44,4,69),(10,45,5,70),(10,46,6,71),(10,10,7,72),(10,11,8,73),(10,12,9,74),(10,13,10,75),(11,12,1,76),(11,13,2,77),(11,9,3,78),(11,10,4,79),(11,11,5,80),(11,1,6,81),(11,2,7,82),(11,6,8,83),(11,7,9,84),(11,8,10,85),(12,14,1,86),(12,15,2,87),(12,16,3,88),(12,17,4,89),(12,18,5,90),(12,19,6,91),(12,3,7,92),(12,4,8,93),(12,12,9,94),(12,13,10,95),(13,1,1,96),(13,3,2,97),(13,5,3,98),(13,24,4,99),(13,30,5,100),(13,35,6,101),(13,41,7,102),(13,6,8,103),(13,14,9,104),(13,20,10,105),(14,8,0,106),(14,1,0,107),(14,6,0,108),(14,10,0,109),(14,11,0,110),(14,9,0,111),(14,7,0,112),(14,2,0,113),(14,12,0,114),(14,13,0,115);
/*!40000 ALTER TABLE `exam_questions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exam_result`
--

DROP TABLE IF EXISTS `exam_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_result` (
  `student_id` int NOT NULL,
  `exam_id` int NOT NULL,
  `score` int NOT NULL,
  `taken_exam` datetime NOT NULL,
  `user_answers` json DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `exam_id` (`exam_id`),
  CONSTRAINT `exam_result_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `student` (`id`),
  CONSTRAINT `exam_result_ibfk_2` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exam_result`
--

LOCK TABLES `exam_result` WRITE;
/*!40000 ALTER TABLE `exam_result` DISABLE KEYS */;
INSERT INTO `exam_result` VALUES (1,1,100,'2025-08-05 23:30:42','{\"1\": 2, \"2\": 5}',1),(1,14,70,'2025-08-05 23:59:37','{\"1\": 2, \"2\": 6, \"6\": 22, \"7\": 26, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',2),(1,10,60,'2025-08-06 00:12:04','{\"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49, \"41\": 161, \"42\": 165, \"43\": 169, \"44\": 173, \"45\": 177, \"46\": 181}',3),(1,3,100,'2025-08-06 00:26:07','{\"5\": 17}',4),(1,2,100,'2025-08-06 11:58:49','{\"3\": 9, \"4\": 13}',5),(1,4,90,'2025-08-06 15:40:49','{\"1\": 2, \"2\": 6, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',6),(1,5,70,'2025-08-06 23:46:26','{\"3\": 9, \"4\": 13, \"14\": 53, \"15\": 60, \"16\": 61, \"17\": 68, \"18\": 70, \"19\": 75, \"20\": 78, \"21\": 81}',7),(1,14,80,'2025-08-07 11:44:28','{\"1\": 2, \"2\": 6, \"6\": 22, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',8),(1,14,90,'2025-08-07 11:46:55','{\"1\": 1, \"2\": 5, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',9),(1,14,100,'2025-08-07 13:30:52','{\"1\": 2, \"2\": 5, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',10),(1,14,0,'2025-08-07 13:32:06','{}',11),(1,6,20,'2025-08-07 20:34:29','{\"1\": 2, \"3\": 9}',12);
/*!40000 ALTER TABLE `exam_result` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exam_session`
--

DROP TABLE IF EXISTS `exam_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_session` (
  `student_id` int NOT NULL,
  `exam_id` int NOT NULL,
  `start_time` datetime NOT NULL,
  `pause_time` datetime DEFAULT NULL,
  `resume_time` datetime DEFAULT NULL,
  `total_paused_duration` int DEFAULT NULL,
  `current_question_index` int DEFAULT NULL,
  `user_answers` json DEFAULT NULL,
  `is_paused` tinyint(1) DEFAULT NULL,
  `is_completed` tinyint(1) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `exam_id` (`exam_id`),
  CONSTRAINT `exam_session_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `student` (`id`),
  CONSTRAINT `exam_session_ibfk_2` FOREIGN KEY (`exam_id`) REFERENCES `exam` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exam_session`
--

LOCK TABLES `exam_session` WRITE;
/*!40000 ALTER TABLE `exam_session` DISABLE KEYS */;
INSERT INTO `exam_session` VALUES (1,10,'2025-08-06 00:11:22',NULL,NULL,0,9,'{\"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49, \"41\": 161, \"42\": 165, \"43\": 169, \"44\": 173, \"45\": 177, \"46\": 181}',0,1,7),(1,3,'2025-08-06 00:13:51',NULL,NULL,0,0,'{}',0,1,8),(1,3,'2025-08-06 00:19:41',NULL,NULL,0,0,'{\"5\": 17}',0,1,9),(1,3,'2025-08-06 00:26:02',NULL,NULL,0,0,'{\"5\": 17}',0,1,10),(1,2,'2025-08-06 10:53:16',NULL,NULL,0,1,'{\"3\": 9, \"4\": 13}',0,1,12),(1,2,'2025-08-06 11:37:09','2025-08-06 11:43:20','2025-08-06 11:58:33',1164,1,'{\"3\": 9, \"4\": 13}',0,1,13),(1,4,'2025-08-06 14:46:27','2025-08-06 15:39:24','2025-08-06 15:39:34',1978,9,'{\"1\": 2, \"2\": 6, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',0,1,14),(1,5,'2025-08-06 23:05:45','2025-08-06 23:15:02','2025-08-06 23:45:38',2157,0,'{\"3\": 9, \"4\": 13, \"14\": 53, \"15\": 60, \"16\": 61, \"17\": 68, \"18\": 70, \"19\": 75, \"20\": 78, \"21\": 81}',0,1,15),(1,14,'2025-08-07 11:43:43',NULL,NULL,0,9,'{\"1\": 2, \"2\": 6, \"6\": 22, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',0,1,16),(1,14,'2025-08-07 11:46:33',NULL,NULL,0,9,'{\"1\": 1, \"2\": 5, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',0,1,17),(1,14,'2025-08-07 13:30:07',NULL,NULL,0,9,'{\"1\": 2, \"2\": 5, \"6\": 21, \"7\": 25, \"8\": 29, \"9\": 33, \"10\": 37, \"11\": 41, \"12\": 45, \"13\": 49}',0,1,22),(1,14,'2025-08-07 13:31:56',NULL,NULL,0,0,'{}',0,1,23),(1,6,'2025-08-07 20:32:30',NULL,NULL,0,8,'{\"1\": 2, \"3\": 9}',0,1,24);
/*!40000 ALTER TABLE `exam_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `question`
--

DROP TABLE IF EXISTS `question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `question` (
  `question_title` varchar(100) NOT NULL,
  `createBy` varchar(50) NOT NULL,
  `createAt` datetime NOT NULL,
  `chapter_id` int NOT NULL,
  `user_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `question_title` (`question_title`),
  KEY `chapter_id` (`chapter_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `question_ibfk_1` FOREIGN KEY (`chapter_id`) REFERENCES `chapter` (`id`),
  CONSTRAINT `question_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `question`
--

LOCK TABLES `question` WRITE;
/*!40000 ALTER TABLE `question` DISABLE KEYS */;
INSERT INTO `question` VALUES ('2 + 2 = ?','admin','2025-08-05 23:16:08',1,1,1),('Nghiệm của phương trình x² - 4 = 0 là:','admin','2025-08-05 23:16:08',1,1,2),('Công thức tính vận tốc là:','admin','2025-08-05 23:16:08',4,1,3),('Gia tốc trọng trường trên Trái Đất là:','admin','2025-08-05 23:16:08',4,1,4),('Công thức hóa học của nước là:','admin','2025-08-05 23:16:08',7,1,5),('3x + 5 = 14, x = ?','admin','2025-08-05 23:16:08',1,1,6),('√16 = ?','admin','2025-08-05 23:16:08',1,1,7),('2³ = ?','admin','2025-08-05 23:16:08',1,1,8),('Diện tích hình vuông cạnh 5cm là:','admin','2025-08-05 23:16:08',2,1,9),('Chu vi hình tròn bán kính 7cm là:','admin','2025-08-05 23:16:08',2,1,10),('Thể tích hình lập phương cạnh 3cm là:','admin','2025-08-05 23:16:08',2,1,11),('Đạo hàm của x² là:','admin','2025-08-05 23:16:08',3,1,12),('∫x dx = ?','admin','2025-08-05 23:16:08',3,1,13),('Định luật Newton thứ nhất nói về:','admin','2025-08-05 23:16:08',4,1,14),('Công thức tính động lượng là:','admin','2025-08-05 23:16:08',4,1,15),('Nhiệt độ sôi của nước ở áp suất tiêu chuẩn:','admin','2025-08-05 23:16:08',5,1,16),('Đơn vị đo nhiệt lượng là:','admin','2025-08-05 23:16:08',5,1,17),('Định luật Ohm có dạng:','admin','2025-08-05 23:16:08',6,1,18),('Điện trở của dây dẫn phụ thuộc vào:','admin','2025-08-05 23:16:08',6,1,19),('Số oxi hóa của H trong H₂O là:','admin','2025-08-05 23:16:08',7,1,20),('Axit mạnh nhất trong các axit sau:','admin','2025-08-05 23:16:08',7,1,21),('Công thức phân tử của methane là:','admin','2025-08-05 23:16:08',8,1,22),('Ancol etylic có công thức:','admin','2025-08-05 23:16:08',8,1,23),('Choose the correct form: \'I ___ to school yesterday\'','admin','2025-08-05 23:16:08',9,1,24),('Which is correct: \'He ___ English very well\'','admin','2025-08-05 23:16:08',9,1,25),('What does \'beautiful\' mean?','admin','2025-08-05 23:16:08',10,1,26),('The opposite of \'big\' is:','admin','2025-08-05 23:16:08',10,1,27),('In the sentence \'The cat is sleeping\', what is the subject?','admin','2025-08-05 23:16:08',11,1,28),('What tense is used in \'I am reading a book\'?','admin','2025-08-05 23:16:08',11,1,29),('Nước Văn Lang được thành lập vào thời gian nào?','admin','2025-08-05 23:16:08',12,1,30),('Ai là người sáng lập ra nước Âu Lạc?','admin','2025-08-05 23:16:08',12,1,31),('Cuộc khởi nghĩa Tây Sơn diễn ra vào thế kỷ nào?','admin','2025-08-05 23:16:08',13,1,32),('Ai là hoàng đế cuối cùng của triều Nguyễn?','admin','2025-08-05 23:16:08',13,1,33),('Cách mạng tháng Tám diễn ra vào năm nào?','admin','2025-08-05 23:16:08',14,1,34),('Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?','admin','2025-08-05 23:16:08',14,1,35),('Núi cao nhất Việt Nam là:','admin','2025-08-05 23:16:08',15,1,36),('Sông dài nhất Việt Nam là:','admin','2025-08-05 23:16:08',15,1,37),('Khu vực kinh tế trọng điểm phía Nam là:','admin','2025-08-05 23:16:08',16,1,38),('Cây trồng chủ yếu ở ĐBSCL là:','admin','2025-08-05 23:16:08',16,1,39),('Dân số Việt Nam hiện tại khoảng:','admin','2025-08-05 23:16:08',17,1,40),('Thành phố có dân số đông nhất Việt Nam là:','admin','2025-08-05 23:16:08',17,1,41),('Bào quan nào chứa DNA trong tế bào?','admin','2025-08-05 23:16:08',18,1,42),('Quá trình phân chia tế bào được gọi là:','admin','2025-08-05 23:16:08',18,1,43),('Gen là gì?','admin','2025-08-05 23:16:08',19,1,44),('DNA có cấu trúc như thế nào?','admin','2025-08-05 23:16:08',19,1,45),('Chuỗi thức ăn bắt đầu từ:','admin','2025-08-05 23:16:08',20,1,46),('Hiệu ứng nhà kính do đâu gây ra?','admin','2025-08-05 23:16:08',20,1,47);
/*!40000 ALTER TABLE `question` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student`
--

DROP TABLE IF EXISTS `student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student` (
  `user_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `student_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student`
--

LOCK TABLES `student` WRITE;
/*!40000 ALTER TABLE `student` DISABLE KEYS */;
INSERT INTO `student` VALUES (2,1),(3,2),(4,3);
/*!40000 ALTER TABLE `student` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subject`
--

DROP TABLE IF EXISTS `subject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subject` (
  `subject_name` varchar(100) NOT NULL,
  `description` text,
  `admin_id` int NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `admin_id` (`admin_id`),
  CONSTRAINT `subject_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subject`
--

LOCK TABLES `subject` WRITE;
/*!40000 ALTER TABLE `subject` DISABLE KEYS */;
INSERT INTO `subject` VALUES ('Toán học','Môn học về các khái niệm toán học cơ bản',1,1),('Vật lý','Môn học về các hiện tượng vật lý',1,2),('Hóa học','Môn học về các phản ứng hóa học',1,3),('Tiếng Anh','Môn học về ngôn ngữ Anh',1,4),('Lịch sử','Môn học về lịch sử Việt Nam và thế giới',1,5),('Địa lý','Môn học về địa lý tự nhiên và kinh tế',1,6),('Sinh học','Môn học về các quá trình sinh học',1,7);
/*!40000 ALTER TABLE `subject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `name` varchar(50) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `email` varchar(50) NOT NULL,
  `avatar` varchar(100) DEFAULT NULL,
  `role` enum('ADMIN','STUDENT') DEFAULT NULL,
  `gender` varchar(6) NOT NULL,
  `createdAt` datetime DEFAULT NULL,
  `updateAt` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES ('Lâm','admin','21232f297a57a5a743894a0e4a801fc3','lamn9049@gmail.com','https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png','ADMIN','Male','2025-08-05 23:16:08','2025-08-05 23:16:08',1),('Nguyễn Văn A','student1','202cb962ac59075b964b07152d234b70','lamn10049@gmail.com','https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png','STUDENT','Male','2025-08-05 23:16:08','2025-08-07 21:54:39',2),('Trần Thị B','student2','202cb962ac59075b964b07152d234b70','2251052057lam@ou.edu.vn','https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png','STUDENT','Female','2025-08-05 23:16:08','2025-08-05 23:16:08',3),('Lê Văn C','student3','202cb962ac59075b964b07152d234b70','student3@example.com','https://res.cloudinary.com/denmq54ke/image/upload/v1752161601/login_register_d1oj9t.png','STUDENT','Male','2025-08-05 23:16:08','2025-08-05 23:16:08',4);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-07 21:56:14
