CREATE TABLE linkedinQuestions (
    questionId INT PRIMARY KEY AUTO_INCREMENT,
    questionText VARCHAR(500) NOT NULL,
    questionType ENUM('Text Input', 'Dropdown', 'Radio Button', 'Multiple Select (Checkbox)') NOT NULL,
    isRequired BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE linkedinQuestionOptions (
    optionId INT PRIMARY KEY AUTO_INCREMENT,
    questionId INT NOT NULL,
    optionText VARCHAR(255),
    FOREIGN KEY (questionId) REFERENCES linkedinQuestions(questionId)
);