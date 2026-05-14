本地直连：
  mysql -h 127.0.0.1 -P 5400 -u mapuser -pmappass mapdb

  连上之后常用命令：
  -- 查看所有表
  SHOW TABLES;

  -- 查看某张表结构
  DESC 表名;

  -- 查看数据（前10行）
  SELECT * FROM 表名 LIMIT 10;

  -- 查看数据总量
  SELECT COUNT(*) FROM 表名;

  如果是 Docker 启动的数据库，也可以直接在容器里查：
  docker exec -it map_backend-tdsql-1 mysql -u mapuser -pmappass mapdb -e "SHOW TABLES;"