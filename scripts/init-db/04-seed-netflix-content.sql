-- ═══════════════════════════════════════════════════════════════
-- Netflix Content Seed — 50 Movies with Real YouTube Trailer IDs
-- ═══════════════════════════════════════════════════════════════
\connect netflix_db;

INSERT INTO netflix_content (title, description, category, youtube_id, thumbnail_url, release_year, rating, duration_minutes, maturity_rating, tags) VALUES
-- ACTION (10)
('The Dark Knight', 'Batman faces the Joker in a battle for Gotham''s soul.', 'Action', 'EXeTwQWrcwY', 'https://img.youtube.com/vi/EXeTwQWrcwY/maxresdefault.jpg', 2008, 9.0, 152, 'PG-13', ARRAY['superhero','thriller','crime']),
('Mad Max: Fury Road', 'In a post-apocalyptic wasteland, Max teams up with Furiosa to escape a tyrant.', 'Action', 'hEJnMQG9ev8', 'https://img.youtube.com/vi/hEJnMQG9ev8/maxresdefault.jpg', 2015, 8.1, 120, 'R', ARRAY['post-apocalyptic','action','chase']),
('John Wick', 'An ex-hitman comes out of retirement to track down the gangsters who took everything.', 'Action', 'C0BMx-qxsP4', 'https://img.youtube.com/vi/C0BMx-qxsP4/maxresdefault.jpg', 2014, 7.4, 101, 'R', ARRAY['revenge','action','thriller']),
('Gladiator', 'A former Roman General sets out to exact vengeance against the corrupt emperor.', 'Action', 'owK1qxDselE', 'https://img.youtube.com/vi/owK1qxDselE/maxresdefault.jpg', 2000, 8.5, 155, 'R', ARRAY['historical','epic','drama']),
('Top Gun: Maverick', 'After thirty years, Maverick is still pushing the envelope as a top naval aviator.', 'Action', 'giXco2jaZ_4', 'https://img.youtube.com/vi/giXco2jaZ_4/maxresdefault.jpg', 2022, 8.3, 130, 'PG-13', ARRAY['aviation','military','sequel']),
('Mission Impossible: Fallout', 'Ethan Hunt and his IMF team race against time after a mission gone wrong.', 'Action', 'wb49-oV0F78', 'https://img.youtube.com/vi/wb49-oV0F78/maxresdefault.jpg', 2018, 7.7, 147, 'PG-13', ARRAY['spy','action','thriller']),
('The Matrix', 'A computer hacker learns about the true nature of his reality.', 'Action', 'vKQi3bBA1y8', 'https://img.youtube.com/vi/vKQi3bBA1y8/maxresdefault.jpg', 1999, 8.7, 136, 'R', ARRAY['sci-fi','cyberpunk','action']),
('Extraction', 'A black-market mercenary is hired to rescue the kidnapped son of a crime lord.', 'Action', 'L6P3nI6VnlY', 'https://img.youtube.com/vi/L6P3nI6VnlY/maxresdefault.jpg', 2020, 6.7, 116, 'R', ARRAY['mercenary','action','rescue']),
('Nobody', 'A bystander intervenes to help a woman being harassed and pulls him into a brutal world.', 'Action', 'wZti8QKBWPo', 'https://img.youtube.com/vi/wZti8QKBWPo/maxresdefault.jpg', 2021, 7.4, 92, 'R', ARRAY['revenge','action','dark-comedy']),
('Avengers: Endgame', 'The Avengers assemble once more to reverse Thanos'' actions and restore balance.', 'Action', 'TcMBFSGVi1c', 'https://img.youtube.com/vi/TcMBFSGVi1c/maxresdefault.jpg', 2019, 8.4, 181, 'PG-13', ARRAY['superhero','ensemble','epic']),

-- DRAMA (10)
('The Shawshank Redemption', 'Two imprisoned men bond over several years, finding solace and redemption.', 'Drama', '6hB3S9bIaco', 'https://img.youtube.com/vi/6hB3S9bIaco/maxresdefault.jpg', 1994, 9.3, 142, 'R', ARRAY['prison','hope','friendship']),
('Forrest Gump', 'The story of a man with a low IQ who accomplished great things in his life.', 'Drama', 'bLvqoHBptjg', 'https://img.youtube.com/vi/bLvqoHBptjg/maxresdefault.jpg', 1994, 8.8, 142, 'PG-13', ARRAY['biography','heartwarming','history']),
('The Godfather', 'The aging patriarch of an organized crime dynasty transfers control to his son.', 'Drama', 'UaVTIH8mujA', 'https://img.youtube.com/vi/UaVTIH8mujA/maxresdefault.jpg', 1972, 9.2, 175, 'R', ARRAY['mafia','crime','family']),
('Schindler''s List', 'In German-occupied Poland, Oskar Schindler saves twelve hundred Jews.', 'Drama', 'gG22XNhtnoY', 'https://img.youtube.com/vi/gG22XNhtnoY/maxresdefault.jpg', 1993, 9.0, 195, 'R', ARRAY['war','biography','historical']),
('Fight Club', 'An insomniac office worker and a soap salesman build a global underground movement.', 'Drama', 'SUXWAEX2jlg', 'https://img.youtube.com/vi/SUXWAEX2jlg/maxresdefault.jpg', 1999, 8.8, 139, 'R', ARRAY['psychological','cult-classic','thriller']),
('Parasite', 'Greed and class discrimination threaten a symbiotic relationship between families.', 'Drama', '5xH0HfJHsaY', 'https://img.youtube.com/vi/5xH0HfJHsaY/maxresdefault.jpg', 2019, 8.5, 132, 'R', ARRAY['thriller','social-commentary','korean']),
('Whiplash', 'A promising young drummer pushes himself to perfection under a ruthless instructor.', 'Drama', '7d_jQycdQGo', 'https://img.youtube.com/vi/7d_jQycdQGo/maxresdefault.jpg', 2014, 8.5, 106, 'R', ARRAY['music','ambition','psychological']),
('The Pursuit of Happyness', 'A struggling salesman takes custody of his son and fights for a better life.', 'Drama', '89Rr5eTfMnk', 'https://img.youtube.com/vi/89Rr5eTfMnk/maxresdefault.jpg', 2006, 8.0, 117, 'PG-13', ARRAY['biography','inspirational','family']),
('Oppenheimer', 'The story of the American scientist who led development of the atomic bomb.', 'Drama', 'uYPbbksJxIg', 'https://img.youtube.com/vi/uYPbbksJxIg/maxresdefault.jpg', 2023, 8.3, 180, 'R', ARRAY['biography','war','history']),
('Joker', 'A mentally troubled stand-up comedian embarks on a downward spiral of violence.', 'Drama', 'zAGVQLHvwOY', 'https://img.youtube.com/vi/zAGVQLHvwOY/maxresdefault.jpg', 2019, 8.4, 122, 'R', ARRAY['psychological','origin-story','dark']),

-- COMEDY (10)
('The Grand Budapest Hotel', 'A legendary concierge and his lobby boy are caught up in theft and murder.', 'Comedy', '1Fg5iWmQjwk', 'https://img.youtube.com/vi/1Fg5iWmQjwk/maxresdefault.jpg', 2014, 8.1, 99, 'R', ARRAY['quirky','adventure','mystery']),
('Superbad', 'Two co-dependent high school seniors set out to score alcohol for a party.', 'Comedy', '4eaZ_48ZGok', 'https://img.youtube.com/vi/4eaZ_48ZGok/maxresdefault.jpg', 2007, 7.6, 113, 'R', ARRAY['teen','coming-of-age','party']),
('The Hangover', 'Three buddies wake up after a bachelor party with no memory and the groom missing.', 'Comedy', 'tcdUhdOlz9M', 'https://img.youtube.com/vi/tcdUhdOlz9M/maxresdefault.jpg', 2009, 7.7, 100, 'R', ARRAY['bachelor-party','adventure','vegas']),
('Knives Out', 'A detective investigates the death of a patriarch of an eccentric family.', 'Comedy', 'xi-1NchUqMA', 'https://img.youtube.com/vi/xi-1NchUqMA/maxresdefault.jpg', 2019, 7.9, 130, 'PG-13', ARRAY['mystery','whodunit','ensemble']),
('Deadpool', 'A wisecracking mercenary gets experimented on and becomes immortal.', 'Comedy', 'ONHBaC-pfsk', 'https://img.youtube.com/vi/ONHBaC-pfsk/maxresdefault.jpg', 2016, 8.0, 108, 'R', ARRAY['superhero','meta','action-comedy']),
('The Truman Show', 'An insurance salesman discovers his entire life is a TV show.', 'Comedy', 'dlnmQbPGuls', 'https://img.youtube.com/vi/dlnmQbPGuls/maxresdefault.jpg', 1998, 8.2, 103, 'PG', ARRAY['satire','philosophical','drama']),
('Jojo Rabbit', 'A young German boy deals with his single mother during WWII as his imaginary friend Hitler helps him.', 'Comedy', 'tL4McUzOhKc', 'https://img.youtube.com/vi/tL4McUzOhKc/maxresdefault.jpg', 2019, 7.9, 108, 'PG-13', ARRAY['satire','war','coming-of-age']),
('The Big Lebowski', 'An unemployed slacker gets drawn into a kidnapping plot after being mistaken for a millionaire.', 'Comedy', 'cd-go0oBF4Y', 'https://img.youtube.com/vi/cd-go0oBF4Y/maxresdefault.jpg', 1998, 8.1, 117, 'R', ARRAY['cult-classic','crime','stoner']),
('Game Night', 'A group of friends get together for game night with unexpected consequences.', 'Comedy', 'qmxMAdV6s4Q', 'https://img.youtube.com/vi/qmxMAdV6s4Q/maxresdefault.jpg', 2018, 7.0, 100, 'R', ARRAY['action-comedy','mystery','ensemble']),
('Free Guy', 'A bank teller discovers he''s a background character in a video game.', 'Comedy', 'X2m-08cOAbc', 'https://img.youtube.com/vi/X2m-08cOAbc/maxresdefault.jpg', 2021, 7.1, 115, 'PG-13', ARRAY['gaming','action-comedy','sci-fi']),

-- DOCUMENTARY (10)
('Planet Earth II', 'David Attenborough returns with a look at the natural world in stunning detail.', 'Documentary', 'c8aFcHFo8SM', 'https://img.youtube.com/vi/c8aFcHFo8SM/maxresdefault.jpg', 2016, 9.5, 300, 'G', ARRAY['nature','wildlife','bbc']),
('The Social Dilemma', 'Tech experts sound the alarm on the dangerous impact of social networking.', 'Documentary', 'uaaC57tcci0', 'https://img.youtube.com/vi/uaaC57tcci0/maxresdefault.jpg', 2020, 7.6, 94, 'PG-13', ARRAY['technology','social-media','warning']),
('Our Planet', 'Documentary series focusing on the breadth of the diversity of habitats around the world.', 'Documentary', 'aETNYyrqNYE', 'https://img.youtube.com/vi/aETNYyrqNYE/maxresdefault.jpg', 2019, 9.3, 350, 'G', ARRAY['nature','climate','netflix-original']),
('13th', 'Explores the intersection of race, justice, and mass incarceration in the US.', 'Documentary', 'krfcq5pF8u8', 'https://img.youtube.com/vi/krfcq5pF8u8/maxresdefault.jpg', 2016, 8.2, 100, 'PG-13', ARRAY['social-justice','race','politics']),
('Free Solo', 'Alex Honnold attempts to become the first person to free solo climb El Capitan.', 'Documentary', 'urRVZ4SW7WU', 'https://img.youtube.com/vi/urRVZ4SW7WU/maxresdefault.jpg', 2018, 8.2, 100, 'PG-13', ARRAY['climbing','extreme-sports','biography']),
('Inside Job', 'Takes a closer look at what caused the financial crisis of 2008.', 'Documentary', 'FzrBurlJUNk', 'https://img.youtube.com/vi/FzrBurlJUNk/maxresdefault.jpg', 2010, 8.2, 109, 'PG-13', ARRAY['finance','economy','investigation']),
('Seaspiracy', 'A filmmaker sets out to document the harm that humans do to marine species.', 'Documentary', '1Q5CXN7soQg', 'https://img.youtube.com/vi/1Q5CXN7soQg/maxresdefault.jpg', 2021, 8.1, 89, 'PG-13', ARRAY['ocean','environment','activism']),
('Blackfish', 'Explores an orca held by SeaWorld and the consequences of keeping them in captivity.', 'Documentary', 'fLOeH-Oq_1Y', 'https://img.youtube.com/vi/fLOeH-Oq_1Y/maxresdefault.jpg', 2013, 8.1, 83, 'PG-13', ARRAY['animals','activism','controversy']),
('The Last Dance', 'Chronicles Michael Jordan and the 1997-98 Chicago Bulls championship season.', 'Documentary', '1LHTP3aukbg', 'https://img.youtube.com/vi/1LHTP3aukbg/maxresdefault.jpg', 2020, 9.1, 500, 'PG-13', ARRAY['sports','basketball','biography']),
('Icarus', 'A cyclist discovers a massive doping scandal while investigating anti-doping tests.', 'Documentary', 'qXoRdSTrR-4', 'https://img.youtube.com/vi/qXoRdSTrR-4/maxresdefault.jpg', 2017, 7.9, 121, 'PG-13', ARRAY['sports','doping','investigation']),

-- SCI-FI (10)
('Interstellar', 'A team of explorers travel through a wormhole in space to ensure humanity''s survival.', 'Sci-Fi', 'zSWdZVtXT7E', 'https://img.youtube.com/vi/zSWdZVtXT7E/maxresdefault.jpg', 2014, 8.7, 169, 'PG-13', ARRAY['space','time','philosophical']),
('Blade Runner 2049', 'A young blade runner discovers a secret that threatens to plunge society into chaos.', 'Sci-Fi', 'gCcx85zbxz4', 'https://img.youtube.com/vi/gCcx85zbxz4/maxresdefault.jpg', 2017, 8.0, 164, 'R', ARRAY['cyberpunk','dystopian','noir']),
('Arrival', 'A linguist works with the military to communicate with alien lifeforms.', 'Sci-Fi', 'tFMo3UJ4B4g', 'https://img.youtube.com/vi/tFMo3UJ4B4g/maxresdefault.jpg', 2016, 7.9, 116, 'PG-13', ARRAY['aliens','linguistics','cerebral']),
('Dune', 'A noble family becomes embroiled in a war for control of the galaxy''s most valuable asset.', 'Sci-Fi', '8g18jFHCLXk', 'https://img.youtube.com/vi/8g18jFHCLXk/maxresdefault.jpg', 2021, 8.0, 155, 'PG-13', ARRAY['epic','desert','politics']),
('Ex Machina', 'A programmer is selected to participate in an experiment with an AI robot.', 'Sci-Fi', 'EoQuVnKhxaM', 'https://img.youtube.com/vi/EoQuVnKhxaM/maxresdefault.jpg', 2014, 7.7, 108, 'R', ARRAY['artificial-intelligence','thriller','philosophical']),
('The Martian', 'An astronaut becomes stranded on Mars and must find a way to survive.', 'Sci-Fi', 'ej3ioOneTy8', 'https://img.youtube.com/vi/ej3ioOneTy8/maxresdefault.jpg', 2015, 8.0, 144, 'PG-13', ARRAY['survival','mars','science']),
('Inception', 'A thief who steals corporate secrets through dream-sharing technology is given a task.', 'Sci-Fi', 'YoHD9XEInc0', 'https://img.youtube.com/vi/YoHD9XEInc0/maxresdefault.jpg', 2010, 8.8, 148, 'PG-13', ARRAY['dreams','heist','mind-bending']),
('Tenet', 'An operative armed with only one word — Tenet — fights for the survival of the world.', 'Sci-Fi', 'LdOM0x0XDgM', 'https://img.youtube.com/vi/LdOM0x0XDgM/maxresdefault.jpg', 2020, 7.3, 150, 'PG-13', ARRAY['time-inversion','spy','cerebral']),
('Annihilation', 'A biologist signs up for an expedition into an environmental disaster zone.', 'Sci-Fi', '89OP78l9oF0', 'https://img.youtube.com/vi/89OP78l9oF0/maxresdefault.jpg', 2018, 6.8, 115, 'R', ARRAY['horror','biology','surreal']),
('Everything Everywhere All at Once', 'A Chinese-American woman gets swept up in an adventure across the multiverse.', 'Sci-Fi', 'wxN1T1qdqzY', 'https://img.youtube.com/vi/wxN1T1qdqzY/maxresdefault.jpg', 2022, 8.0, 139, 'R', ARRAY['multiverse','comedy','martial-arts'])

ON CONFLICT DO NOTHING;
