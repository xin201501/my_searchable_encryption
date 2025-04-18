use actix_web::middleware::Logger;
use actix_web::{App, HttpServer};
use env_logger::Env;
use sort_enc_results::sort_encrypted_results;
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(Env::default().default_filter_or("info"));
    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .wrap(Logger::new("%a %{User-Agent}i"))
            .service(sort_encrypted_results)
    })
    .bind("0.0.0.0:8003")?
    .run()
    .await
}
