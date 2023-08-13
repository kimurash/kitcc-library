INSERT INTO user (username, password)
VALUES
  ('alice', 'pbkdf2:sha256:260000$AZN7lXpAalAR3t9i$033db28a99e672c758124818bddf90f8189531e28661563ceef679705ac60d9e'),
  ('bob', 'pbkdf2:sha256:260000$6OrlucO8Sjt67Jjn$8f207dab5413a313076714621eb917ef74e77c83fa3df8bb3acec1811be29e1c');

INSERT INTO book (ISBN, title, author, publisher, stock)
VALUES
  ('9784873115658', 'リーダブルコード', 'Dustin Boswell', 'オライリー・ジャパン', 1);