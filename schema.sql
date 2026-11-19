-- ========================================================
-- ABS Student Enrollment Mini Portal - MySQL Schema & Seed
-- ========================================================

CREATE DATABASE IF NOT EXISTS `student_portal` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `student_portal`;

-- --------------------------------------------------------
-- Drop tables in reverse-dependency order
-- --------------------------------------------------------
DROP TABLE IF EXISTS `enrollments`;
DROP TABLE IF EXISTS `courses`;
DROP TABLE IF EXISTS `teachers`;
DROP TABLE IF EXISTS `students`;

-- --------------------------------------------------------
-- Table structure for table `students`
-- --------------------------------------------------------
CREATE TABLE `students` (
  `student_id` VARCHAR(10) NOT NULL PRIMARY KEY,
  `full_name` VARCHAR(100) NOT NULL,
  `grade` INT NOT NULL CHECK (grade BETWEEN 1 AND 12),
  `date_of_birth` DATE NOT NULL,
  `gender` ENUM('Male', 'Female') NOT NULL DEFAULT 'Male',
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `parent_name` VARCHAR(100) DEFAULT NULL,
  `parent_phone` VARCHAR(20) DEFAULT NULL,
  `status` ENUM('Active', 'Withdrawn') NOT NULL DEFAULT 'Active',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_student_id` (`student_id`),
  INDEX `idx_email` (`email`),
  INDEX `idx_status` (`status`),
  INDEX `idx_grade` (`grade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for table `teachers`
-- --------------------------------------------------------
CREATE TABLE `teachers` (
  `teacher_id` VARCHAR(10) NOT NULL PRIMARY KEY CHECK (teacher_id REGEXP '^[0-9]+$'),
  `full_name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) UNIQUE,
  INDEX `idx_teacher_id` (`teacher_id`),
  INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for table `courses`
-- --------------------------------------------------------
CREATE TABLE `courses` (
  `course_code` VARCHAR(10) NOT NULL PRIMARY KEY,
  `title` VARCHAR(100) NOT NULL,
  `grade_level` INT NOT NULL,
  `teacher_id` VARCHAR(10) DEFAULT NULL,
  `capacity` INT NOT NULL,
  INDEX `idx_course_code` (`course_code`),
  INDEX `idx_title` (`title`),
  INDEX `idx_teacher_id` (`teacher_id`),
  CONSTRAINT `fk_course_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for table `enrollments`
-- --------------------------------------------------------
CREATE TABLE `enrollments` (
  `enrollment_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `student_id` VARCHAR(10) NOT NULL,
  `course_code` VARCHAR(10) NOT NULL,
  `term` VARCHAR(10) DEFAULT NULL,
  INDEX `idx_enrollment_id` (`enrollment_id`),
  INDEX `idx_term` (`term`),
  INDEX `idx_student_enrollment` (`student_id`),
  INDEX `idx_course_enrollment` (`course_code`),
  CONSTRAINT `fk_enrollment_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_enrollment_course` FOREIGN KEY (`course_code`) REFERENCES `courses` (`course_code`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Sample initial records for testing
-- --------------------------------------------------------
INSERT INTO `teachers` (`teacher_id`, `full_name`, `email`) VALUES
('1', 'Sarah Collins', 'sarah.collins@school.test'),
('2', 'Ahmed Mansour', 'ahmed.mansour@school.test'),
('3', 'Priya Nair', 'priya.nair@school.test'),
('4', 'David Miller', 'david.miller@school.test'),
('5', 'Layla Hassan', 'layla.hassan@school.test'),
('6', 'John Matthews', 'john.matthews@school.test');

INSERT INTO `courses` (`course_code`, `title`, `grade_level`, `teacher_id`, `capacity`) VALUES
('MTH101', 'Algebra 1', 9, '1', 22),
('MTH201', 'Geometry', 10, '1', 22),
('MTH301', 'Pre-Calculus', 11, '1', 20),
('ENG101', 'English 9', 9, '2', 24),
('ENG201', 'English 10', 10, '2', 24),
('ENG301', 'English 11', 11, '2', 6),
('SCI101', 'Biology', 9, '3', 22),
('SCI201', 'Chemistry', 10, '3', 6),
('SCI301', 'Physics', 11, '3', 20),
('CSC101', 'Intro to Computing', 9, '4', 18),
('CSC201', 'Programming', 10, '4', 18),
('HIS101', 'World History', 10, '5', 24),
('ART101', 'Art', 9, '6', 15),
('PE101', 'Physical Education', 9, '6', 40);

INSERT INTO `students` (`student_id`, `full_name`, `grade`, `date_of_birth`, `gender`, `email`, `status`) VALUES
('S1001', 'Alice Nguyen',      9,  '2009-03-12', 'Female', 's1001@school.test', 'Active'),
('S1002', 'Brian Okafor',     10,  '2008-07-04', 'Male',   's1002@school.test', 'Active'),
('S1003', 'Carla Reyes',      11,  '2007-11-19', 'Female', 's1003@school.test', 'Active'),
('S1004', 'Daniel Kim',        9,  '2009-01-28', 'Male',   's1004@school.test', 'Active'),
('S1005', 'Eva Martinez',      9,  '2009-05-30', 'Female', 's1005@school.test', 'Active'),
('S1006', 'Felix Turner',     10,  '2008-09-15', 'Male',   's1006@school.test', 'Active'),
('S1007', 'Grace Liu',        11,  '2007-02-22', 'Female', 's1007@school.test', 'Active'),
('S1008', 'Henry Patel',       9,  '2009-06-11', 'Male',   's1008@school.test', 'Active'),
('S1009', 'Isla Brown',        9,  '2009-08-03', 'Female', 's1009@school.test', 'Active'),
('S1010', 'James Wilson',     10,  '2008-12-25', 'Male',   's1010@school.test', 'Active'),
('S1011', 'Karen Adams',      11,  '2007-04-14', 'Female', 's1011@school.test', 'Active'),
('S1012', 'Liam Scott',        9,  '2009-10-07', 'Male',   's1012@school.test', 'Active'),
('S1013', 'Mia Robinson',      9,  '2009-02-18', 'Female', 's1013@school.test', 'Active'),
('S1014', 'Noah Carter',      10,  '2008-03-29', 'Male',   's1014@school.test', 'Active'),
('S1015', 'Olivia Hall',      11,  '2007-07-08', 'Female', 's1015@school.test', 'Active'),
('S1016', 'Patrick Young',     9,  '2009-11-01', 'Male',   's1016@school.test', 'Active'),
('S1017', 'Quinn Harris',      9,  '2009-04-23', 'Female', 's1017@school.test', 'Active'),
('S1018', 'Ryan Lewis',       10,  '2008-06-16', 'Male',   's1018@school.test', 'Active'),
('S1019', 'Sara Walker',      11,  '2007-09-05', 'Female', 's1019@school.test', 'Active'),
('S1020', 'Tyler Allen',       9,  '2009-12-20', 'Male',   's1020@school.test', 'Active'),
('S1021', 'Uma Patel',         9,  '2009-01-09', 'Female', 's1021@school.test', 'Active'),
('S1022', 'Victor Cruz',      10,  '2008-05-27', 'Male',   's1022@school.test', 'Active'),
('S1023', 'Wendy Morgan',     11,  '2007-03-13', 'Female', 's1023@school.test', 'Active'),
('S1024', 'Xander Brooks',     9,  '2009-07-31', 'Male',   's1024@school.test', 'Active'),
('S1025', 'Yara Sanders',      9,  '2009-09-18', 'Female', 's1025@school.test', 'Active'),
('S1026', 'Zack Coleman',     10,  '2008-11-06', 'Male',   's1026@school.test', 'Active'),
('S1027', 'Amy Bell',         11,  '2007-01-24', 'Female', 's1027@school.test', 'Active'),
('S1028', 'Ben Foster',        9,  '2009-03-02', 'Male',   's1028@school.test', 'Active'),
('S1029', 'Chloe Rivera',      9,  '2009-08-14', 'Female', 's1029@school.test', 'Active'),
('S1030', 'Derek Hughes',     10,  '2008-04-21', 'Male',   's1030@school.test', 'Active'),
('S1031', 'Ella Price',       11,  '2007-06-10', 'Female', 's1031@school.test', 'Active'),
('S1032', 'Frank Flores',      9,  '2009-10-28', 'Male',   's1032@school.test', 'Active'),
('S1033', 'Gina Ross',         9,  '2009-02-05', 'Female', 's1033@school.test', 'Active'),
('S1034', 'Harry Butler',     10,  '2008-07-19', 'Male',   's1034@school.test', 'Active'),
('S1035', 'Irene Simmons',    11,  '2007-05-03', 'Female', 's1035@school.test', 'Active'),
('S1036', 'Jake Reed',         9,  '2009-12-12', 'Male',   's1036@school.test', 'Active'),
('S1037', 'Kate Barnes',       9,  '2009-04-07', 'Female', 's1037@school.test', 'Active'),
('S1038', 'Leo Griffin',      10,  '2008-08-30', 'Male',   's1038@school.test', 'Active'),
('S1039', 'Mara Diaz',        11,  '2007-10-16', 'Female', 's1039@school.test', 'Active'),
('S1040', 'Nate Hayes',        9,  '2009-06-24', 'Male',   's1040@school.test', 'Active');

INSERT INTO `enrollments` (`student_id`, `course_code`, `term`) VALUES
('S1001', 'CSC101', '2026-T1'),
('S1001', 'ENG101', '2026-T1'),
('S1001', 'ART101', '2026-T1'),
('S1001', 'SCI101', '2026-T1'),
('S1002', 'CSC201', '2026-T1'),
('S1002', 'SCI201', '2026-T1'),
('S1002', 'MTH201', '2026-T1'),
('S1002', 'PE101',  '2026-T1'),
('S1003', 'SCI301', '2026-T1'),
('S1003', 'ENG301', '2026-T1'),
('S1003', 'PE101',  '2026-T1'),
('S1003', 'MTH301', '2026-T1'),
('S1004', 'PE101',  '2026-T1'),
('S1005', 'CSC101', '2026-T1'),
('S1005', 'SCI101', '2026-T1'),
('S1005', 'ART101', '2026-T1'),
('S1005', 'MTH101', '2026-T1'),
('S1006', 'ENG201', '2026-T1'),
('S1006', 'MTH201', '2026-T1'),
('S1006', 'PE101',  '2026-T1'),
('S1006', 'CSC201', '2026-T1'),
('S1007', 'ENG301', '2026-T1'),
('S1007', 'PE101',  '2026-T1'),
('S1007', 'MTH301', '2026-T1'),
('S1007', 'SCI301', '2026-T1'),
('S1008', 'PE101',  '2026-T1'),
('S1009', 'CSC101', '2026-T1'),
('S1009', 'SCI101', '2026-T1'),
('S1009', 'MTH101', '2026-T1'),
('S1009', 'ART101', '2026-T1'),
('S1010', 'MTH201', '2026-T1'),
('S1010', 'CSC201', '2026-T1'),
('S1010', 'ENG201', '2026-T1'),
('S1010', 'HIS101', '2026-T1'),
('S1011', 'ENG301', '2026-T1'),
('S1011', 'PE101',  '2026-T1'),
('S1011', 'SCI301', '2026-T1'),
('S1011', 'MTH301', '2026-T1'),
('S1012', 'PE101',  '2026-T1'),
('S1013', 'CSC101', '2026-T1'),
('S1013', 'PE101',  '2026-T1'),
('S1013', 'MTH101', '2026-T1'),
('S1013', 'SCI101', '2026-T1'),
('S1014', 'ENG201', '2026-T1'),
('S1014', 'PE101',  '2026-T1'),
('S1014', 'HIS101', '2026-T1'),
('S1014', 'MTH201', '2026-T1'),
('S1015', 'ENG301', '2026-T1'),
('S1015', 'SCI301', '2026-T1'),
('S1015', 'PE101',  '2026-T1'),
('S1015', 'MTH301', '2026-T1'),
('S1016', 'PE101',  '2026-T1'),
('S1017', 'PE101',  '2026-T1'),
('S1017', 'SCI101', '2026-T1'),
('S1017', 'ENG101', '2026-T1'),
('S1017', 'ART101', '2026-T1'),
('S1018', 'HIS101', '2026-T1'),
('S1018', 'ENG201', '2026-T1'),
('S1018', 'MTH201', '2026-T1'),
('S1018', 'CSC201', '2026-T1'),
('S1019', 'MTH301', '2026-T1'),
('S1019', 'SCI301', '2026-T1'),
('S1019', 'PE101',  '2026-T1'),
('S1019', 'ENG301', '2026-T1'),
('S1020', 'PE101',  '2026-T1'),
('S1021', 'ENG101', '2026-T1'),
('S1021', 'MTH101', '2026-T1'),
('S1021', 'SCI101', '2026-T1'),
('S1021', 'ART101', '2026-T1'),
('S1022', 'SCI201', '2026-T1'),
('S1022', 'HIS101', '2026-T1'),
('S1022', 'ENG201', '2026-T1'),
('S1022', 'PE101',  '2026-T1'),
('S1023', 'SCI301', '2026-T1'),
('S1023', 'ENG301', '2026-T1'),
('S1023', 'PE101',  '2026-T1'),
('S1023', 'MTH301', '2026-T1'),
('S1024', 'PE101',  '2026-T1'),
('S1025', 'PE101',  '2026-T1'),
('S1025', 'SCI101', '2026-T1'),
('S1025', 'CSC101', '2026-T1'),
('S1025', 'ART101', '2026-T1'),
('S1026', 'HIS101', '2026-T1'),
('S1026', 'PE101',  '2026-T1'),
('S1026', 'CSC201', '2026-T1'),
('S1026', 'SCI201', '2026-T1'),
('S1027', 'SCI301', '2026-T1'),
('S1027', 'MTH301', '2026-T1'),
('S1027', 'PE101',  '2026-T1'),
('S1028', 'PE101',  '2026-T1'),
('S1029', 'ENG101', '2026-T1'),
('S1029', 'ART101', '2026-T1'),
('S1029', 'MTH101', '2026-T1'),
('S1029', 'CSC101', '2026-T1'),
('S1030', 'ENG201', '2026-T1'),
('S1030', 'PE101',  '2026-T1'),
('S1030', 'CSC201', '2026-T1'),
('S1030', 'SCI201', '2026-T1'),
('S1031', 'MTH301', '2026-T1'),
('S1031', 'SCI301', '2026-T1'),
('S1031', 'PE101',  '2026-T1'),
('S1032', 'PE101',  '2026-T1'),
('S1033', 'MTH101', '2026-T1'),
('S1033', 'ART101', '2026-T1'),
('S1033', 'PE101',  '2026-T1'),
('S1033', 'CSC101', '2026-T1'),
('S1034', 'ENG201', '2026-T1'),
('S1034', 'SCI201', '2026-T1'),
('S1034', 'MTH201', '2026-T1'),
('S1034', 'CSC201', '2026-T1'),
('S1035', 'PE101',  '2026-T1'),
('S1035', 'SCI301', '2026-T1'),
('S1035', 'MTH301', '2026-T1'),
('S1036', 'PE101',  '2026-T1'),
('S1037', 'SCI101', '2026-T1'),
('S1037', 'ART101', '2026-T1'),
('S1037', 'ENG101', '2026-T1'),
('S1037', 'PE101',  '2026-T1'),
('S1038', 'SCI201', '2026-T1'),
('S1038', 'CSC201', '2026-T1'),
('S1038', 'HIS101', '2026-T1'),
('S1038', 'PE101',  '2026-T1'),
('S1039', 'SCI301', '2026-T1'),
('S1039', 'PE101',  '2026-T1'),
('S1039', 'MTH301', '2026-T1'),
('S1040', 'PE101',  '2026-T1');
