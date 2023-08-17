INSERT INTO user (username, password)
VALUES
  ('alice', 'pbkdf2:sha256:260000$AZN7lXpAalAR3t9i$033db28a99e672c758124818bddf90f8189531e28661563ceef679705ac60d9e');

INSERT INTO book (ISBN, title, author, publisher, stock)
VALUES
  ('9784873115658', 'リーダブルコード', 'Dustin Boswell', 'オライリー・ジャパン', 1);