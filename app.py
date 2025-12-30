from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# 기본 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///funding.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(
    app.root_path, 'static/uploads'
)

db = SQLAlchemy(app)

# =====================
# DB 모델
# =====================

class Funding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    product_link = db.Column(db.String(500))
    image = db.Column(db.String(200))
    target_amount = db.Column(db.Integer)
    admin_password = db.Column(db.String(100))
    bank = db.Column(db.String(100))
    account = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funding_id = db.Column(db.Integer, db.ForeignKey('funding.id'))
    name = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    message = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =====================
# 라우트
# =====================

@app.route("/")
def home():
    return redirect(url_for("create"))

# 상품 등록
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form["title"]
        product_link = request.form["product_link"]
        target_amount = int(request.form["target_amount"])
        image_file = request.files["image"]

        filename = image_file.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        bank = request.form["bank"]
        account = request.form["account"]

        admin_password = request.form["admin_password"]

        funding = Funding(
            title=title,
            product_link=product_link,
            target_amount=target_amount,
            image=filename,
            account=account,
            bank = bank,
            admin_password=admin_password
        )
        db.session.add(funding)
        db.session.commit()

        return redirect(url_for("funding", funding_id=funding.id))

    return render_template("create.html")

# 펀딩 페이지
@app.route("/funding/<int:funding_id>", methods=["GET", "POST"])
def funding(funding_id):
    funding = Funding.query.get_or_404(funding_id)

    total =db.session.query(
        db.func.sum(Contribution.amount)
    ).filter_by(funding_id=funding_id).scalar() or 0

    is_admin = request.args.get("admin") == funding.admin_password

    if request.method == "POST":

        if total >= funding.target_amount: 
            return redirect(url_for("funding", funding_id=funding.id))
        
        name = request.form["name"]
        amount = int(request.form["amount"])
        message = request.form["message"]

        contribution = Contribution(
            funding_id=funding.id,
            name=name,
            amount=amount,
            message=message
        )
        db.session.add(contribution)
        db.session.commit()

        return jsonify({"status": "success"})

    # 현재 총액
    total = db.session.query(
        db.func.sum(Contribution.amount)
    ).filter_by(funding_id=funding.id).scalar() or 0

    # 입금자 목록
    contributions = Contribution.query.filter_by(
        funding_id = funding.id
    ).order_by(Contribution.created_at.desc()).all()

    percent = min(int((total / funding.target_amount) * 100),100)
    remaining = funding.target_amount - total

    return render_template(
        "funding.html",
        funding=funding,
        total=total,
        percent=percent,
        remaining=remaining,
        contributions=contributions,
        is_admin = is_admin
    )

# =====================
# 실행
# =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
