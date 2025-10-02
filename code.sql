-- Create Database
CREATE DATABASE cinetrack;
USE cinetrack;

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Movies Table
CREATE TABLE movies (
    movie_id INT AUTO_INCREMENT PRIMARY KEY,
    movie_name VARCHAR(200) NOT NULL,
    release_date DATE,
    duration INT,
    description TEXT,
    language VARCHAR(50)
);

-- Genres Table
CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL UNIQUE
);

-- Cast Members Table (renamed from cast)
CREATE TABLE cast_members (
    cast_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dob DATE,
    bio TEXT,
    age INT
);

-- Studios Table
CREATE TABLE studios (
    studio_id INT AUTO_INCREMENT PRIMARY KEY,
    studio_name VARCHAR(100) NOT NULL,
    country VARCHAR(50)
);

-- Streaming Platforms Table
CREATE TABLE streaming_platforms (
    platform_id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(100) NOT NULL,
    subscription_type VARCHAR(50)
);

-- Episodes Table
CREATE TABLE episodes (
    episode_id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    episode_number INT NOT NULL,
    season_number INT NOT NULL DEFAULT 1,
    title VARCHAR(200),
    duration INT,
    air_date DATE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

-- Reviews and Ratings Table
CREATE TABLE reviews_ratings (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating DECIMAL(2,1),
    comment TEXT,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

-- Movie-Genre Junction Table
CREATE TABLE movie_genre (
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- Movie-Cast Junction Table
CREATE TABLE movie_cast (
    movie_id INT NOT NULL,
    cast_id INT NOT NULL,
    role VARCHAR(100),
    character_name VARCHAR(100),
    PRIMARY KEY (movie_id, cast_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (cast_id) REFERENCES cast_members(cast_id) ON DELETE CASCADE
);

-- Movie-Studio Junction Table
CREATE TABLE movie_studio (
    movie_id INT NOT NULL,
    studio_id INT NOT NULL,
    PRIMARY KEY (movie_id, studio_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (studio_id) REFERENCES studios(studio_id) ON DELETE CASCADE
);

-- Movie-Platform Junction Table
CREATE TABLE movie_platform (
    movie_id INT NOT NULL,
    platform_id INT NOT NULL,
    availability_date DATE,
    PRIMARY KEY (movie_id, platform_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES streaming_platforms(platform_id) ON DELETE CASCADE
);

-- Movie Distribution Table
CREATE TABLE movie_distribution (
    distribution_id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    studio_id INT NOT NULL,
    platform_id INT NOT NULL,
    distribution_date DATE,
    territory VARCHAR(100) DEFAULT 'worldwide',
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (studio_id) REFERENCES studios(studio_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES streaming_platforms(platform_id) ON DELETE CASCADE
);

-- User Follow Table (Recursive Relationship)
CREATE TABLE user_follow (
    follower_id INT NOT NULL,
    followed_id INT NOT NULL,
    follow_date DATE DEFAULT (CURRENT_DATE),
    PRIMARY KEY (follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK (follower_id != followed_id)
);

-- Contains Episodes Table
CREATE TABLE contains_episodes (
    episode_id INT PRIMARY KEY,
    movie_id INT NOT NULL,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

-- Donations Table
CREATE TABLE donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    donation_amount DECIMAL(10,2) NOT NULL,
    donation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
DELIMITER $$
CREATE TRIGGER after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO donations (user_id, donation_amount, comment)
    VALUES (NEW.user_id, 0.00, 'Welcome, user created!');
END$$
DELIMITER ;
CREATE TABLE ratings_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT,
    old_rating DECIMAL(2,1),
    new_rating DECIMAL(2,1),
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

DELIMITER $$
CREATE TRIGGER before_rating_update
BEFORE UPDATE ON reviews_ratings
FOR EACH ROW
BEGIN
    IF OLD.rating <> NEW.rating THEN
        INSERT INTO ratings_audit (review_id, old_rating, new_rating)
        VALUES (OLD.review_id, OLD.rating, NEW.rating);
    END IF;
END$$
DELIMITER ;
DELIMITER $$
CREATE PROCEDURE add_genre(IN gen_name VARCHAR(50))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM genres WHERE genre_name = gen_name) THEN
        INSERT INTO genres (genre_name) VALUES (gen_name);
    END IF;
END$$
DELIMITER ;
DELIMITER $$
CREATE PROCEDURE update_studio_country(IN sid INT, IN country_name VARCHAR(50))
BEGIN
    UPDATE studios SET country = country_name WHERE studio_id = sid;
END$$
DELIMITER ;
DELIMITER $$
CREATE FUNCTION total_donations(uid INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2) DEFAULT 0;
    SELECT SUM(donation_amount) INTO total FROM donations WHERE user_id = uid;
    RETURN IFNULL(total,0.00);
END$$
DELIMITER ;
DELIMITER $$
CREATE FUNCTION calc_age(dob DATE) 
RETURNS INT
DETERMINISTIC
RETURN TIMESTAMPDIFF(YEAR, dob, CURDATE());
$$
DELIMITER ;

-- User Watchlists Table
CREATE TABLE watchlists (
    watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    UNIQUE KEY unique_watchlist (user_id, movie_id)
);

