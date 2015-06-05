-- Host: localhost    Database: rldb
use rldb;
DROP TABLE IF EXISTS `friends`;
CREATE TABLE `friends` (
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `firstName` varchar(10) NOT NULL,
  `lastName` varchar(10) NOT NULL,
  `DOB` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `friends`
--

INSERT INTO `friends` VALUES (1,'John','Smith','1975-01-12'),(2,'Jane','Bloggs','1977-02-01'),(3,'Yamada','Taro','1980-03-10'),(4,'Nai','Gor','1985-05-20');
