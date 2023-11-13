
from fastapi import FastAPI, Request, Response, Depends, UploadFile, HTTPException, Cookie, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from database import *
from auth.auth_handler import *
from auth.auth_bearer import JWTBearer

import transaction
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        id = token["id"]
        role = token["role"]
        username = f"{get_user(id).first_name} {get_user(id).last_name}"
        return templates.TemplateResponse("index.html", {"request": request, "alreadylogin": True, "username": username, "role": role})
    except:
        return templates.TemplateResponse("index.html", {"request": request, "alreadylogin": False})
    
@app.on_event("shutdown")
async def shutdown():
    transaction.commit()
    db.close()

# == connect to login page ============================================================
@app.get("/logout", response_class=HTMLResponse)
async def logout(response: Response, request: Request):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/", status_code=302, headers={"Set-Cookie": f"access_token={None}; Path=/"})

# == connect to about page ============================================================
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "invalid": False})

# == connect to admission page ============================================================
@app.get("/admission", response_class=HTMLResponse)
async def admission(request: Request):
    return templates.TemplateResponse("admission.html", {"request": request, "invalid": False})

# == connect to news page ============================================================
@app.get("/news", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news.html", {"request": request, "invalid": False})
@app.get("/news1", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news1.html", {"request": request, "invalid": False})
@app.get("/news2", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news2.html", {"request": request, "invalid": False})
@app.get("/news3", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news3.html", {"request": request, "invalid": False})
@app.get("/news4", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news4.html", {"request": request, "invalid": False})



# == connect to program page ============================================================
@app.get("/program", response_class=HTMLResponse)
async def program(request: Request):
    return templates.TemplateResponse("program.html", {"request": request, "invalid": False})

@app.get("/se2022", response_class=HTMLResponse)
async def se2022(request: Request):
    return templates.TemplateResponse("se2022.html", {"request": request, "invalid": False})

@app.get("/se2024", response_class=HTMLResponse)
async def se2024(request: Request):
    return templates.TemplateResponse("se2024.html", {"request": request, "invalid": False})

@app.get("/glasgow", response_class=HTMLResponse)
async def glasgow(request: Request):
    return templates.TemplateResponse("glasgow.html", {"request": request, "invalid": False})

@app.get("/queensland", response_class=HTMLResponse)
async def queensland(request: Request):
    return templates.TemplateResponse("queensland.html", {"request": request, "invalid": False})




# == connect to studyanytime page ============================================================
@app.get("/studyanytime", response_class=HTMLResponse)
async def studyanytime(request: Request, access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        id = token["id"]
        role = token["role"]
        username = f"{get_user(id).first_name} {get_user(id).last_name}"
        
        root_db = None
        match role:
            case "student":
                root_db = root.student
                id = int(id)
            case "lecturer":
                root_db = root.instructor
                id = int(id)
            case "others":
                root_db = root.otherUser
            case _:
                raise HTTPException(404, detail="value_error: Invalid role")
            
        enrolled_courses = get_course_names(int(id), root_db)
        enrolled_id = [element[0] for element in enrolled_courses]
        
        available_courses = []
        for course in root.course.keys():
            if course not in enrolled_id:
                available_courses.append([course, root.course[course].name])
        
        print(role)
        return templates.TemplateResponse("studyanytime.html", {"request": request, "alreadylogin": True, "username": username, "role": role, "enrolled_courses" : enrolled_courses, "available_courses": available_courses})
    except Exception as e:
        print("error" + str(e))
        return templates.TemplateResponse("studyanytime.html", {"request": request, "alreadylogin": False})

# == connect to login page ============================================================
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "invalid": False})

# == connect to sign up page ==========================================================
@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "invalid": False})

# == connect to resetpassword page ====================================================
@app.get("/resetpassword", response_class=HTMLResponse)
async def resetpassword(request: Request):
    return templates.TemplateResponse("resetpassword.html", {"request": request})

# == CLEAR DB ====================================================
@app.delete("/clear_user_db")
async def clear_user_db():
    root.instructor = BTrees.OOBTree.BTree()
    root.student = BTrees.OOBTree.BTree()
    root.otherUser = BTrees.OOBTree.BTree()
    
@app.delete("/clear_course_db")
async def clear_course_db():
    root.course = BTrees.OOBTree.BTree()

# == VERIFY JWT ====================================================
@app.get("/verify_token")
async def verify_token(request: Request, access_token: str = Cookie(None)):
    if decodeJWT(access_token) == None:
        return False
    else:
        return True

# == VIDEO PLAYER =====================================================================
videos_directory = Path("db/course_videos")

@app.get("/video/{course_id}/{filename}")
async def get_video(course_id: int, filename: str):
    video_path = videos_directory / str(course_id) / filename
    try:
        if not course_id in root.course.keys():
            raise HTTPException(404, detail="db_error: Course not found")

        if not root.course[course_id].isIn(Video(filename)):
            raise HTTPException(404, detail="db_error: Video not found")

        if not video_path.is_file():
            raise HTTPException(404, detail="fs_error: Video not found")

        return FileResponse(video_path, headers={"Accept-Ranges": "bytes"})
    except Exception as e:
        raise e

@app.post("/video/upload/{course_id}/{instructor_id}")
async def upload_file(course_id: int, instructor_id: int, file: UploadFile):
    course_directory = videos_directory / str(course_id)
    try:
        if not instructor_id in root.instructor.keys():
            raise HTTPException(404, detail="db_error: Instructor not found")

        file_path = course_directory / file.filename

        if root.course[course_id].isIn(Video(file.filename)):
            raise HTTPException(404, detail="db_error: Video with the same filename already exists")

        if file_path.is_file():
            raise HTTPException(404, detail="fs_error: Video with the same filename already exists")

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        temp_course = Course(root.course[course_id].id, root.course[course_id].name, root.course[course_id].instructor, root.course[course_id].public)
        for c in root.course[course_id].videos:
            temp_course.addVideo(c)
        temp_course.addVideo(file.filename)
        root.course[course_id] = temp_course
        
        transaction.commit()

        return {"message": "Video uploaded successfully"}
    except Exception as e:
        raise e

# == USER HANDLER=======================================================================
@app.post("/user/signIn/")
async def signIn(response: Response, request: Request, id: str = Form(...), password: str = Form(...), role: str = Form(...)):
    try:
        root_db = None
        match role:
            case "student":
                root_db = root.student
                id = int(id)
            case "lecturer":
                root_db = root.instructor
                id = int(id)
            case "others":
                root_db = root.otherUser
            case _:
                raise HTTPException(404, detail="value_error: Invalid role")

        if check_user(root_db, id, password):
            access_token = signJWT(id, role)
            response.set_cookie(key="access_token", value=access_token)
            
            return RedirectResponse(url="/", status_code=302, headers={"Set-Cookie": f"access_token={access_token}; Path=/"})
        
        raise Exception 
    except Exception:
        return templates.TemplateResponse("login.html", {"request": request, "invalid": True})
  
@app.post("/user/signUp/")
async def signUp(response: Response, request: Request, id: str = Form(...), first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...)):
    try:
        if ((int(id) in root.student.keys()) or (int(id) in root.instructor.keys()) or (id in root.otherUser.keys())):
            raise HTTPException(404, detail="db_error: User already exists")
        
        match role:
            case "student":
                root_db = root.student
                id = int(id)
                root_db[id] = Student(id, first_name, last_name, email, password)
            case "lecturer":
                root_db = root.instructor
                id = int(id)
                root_db[id] = Instructor(id, first_name, last_name, email, password)
            case "others":
                root_db = root.otherUser
                root_db[id] = OtherUser(id, first_name, last_name, email, password)
            case _:
                raise HTTPException(404, detail="value_error: Invalid role")
        
        transaction.commit()
        
        access_token = signJWT(id, role)
        response.status_code = 200
        response.set_cookie(key="access_token", value=access_token)
        
        return RedirectResponse(url="/", status_code=302, headers={"Set-Cookie": f"access_token={access_token}; Path=/"})
    except Exception as e:
        return templates.TemplateResponse("signup.html", {"request": request, "invalid": True})

@app.get("/enroll/{role}/{user_id}/{course_id}")
async def enroll(role: str, user_id: str, course_id: int):
    try:
        
        user = get_user(int(user_id))
        if course_id in user.courses:
            raise HTTPException(404, detail="Already Enrolled")
        
        course = await get_course(course_id)
        
        match role:
            case "student":
                user_id = int(user_id)
                temp_user = Student(root.student[user_id].id, root.student[user_id].first_name, root.student[user_id].last_name, root.student[user_id].email, root.student[user_id].password)
                for c in root.student[user_id].courses:
                    temp_user.enrollCourse(c)
                temp_user.enrollCourse(course.id)
                root.student[user_id] = temp_user
            case "others":
                temp_user = OtherUser(root.otherUser[user_id].id, root.otherUser[user_id].first_name, root.otherUser[user_id].last_name, root.otherUser[user_id].email, root.otherUser[user_id].password)
                for c in root.otherUser[user_id].courses:
                    temp_user.enrollCourse(c)
                temp_user.enrollCourse(course.id)
                root.otherUser[user_id] = temp_user
            case _:
                raise HTTPException(404, detail="value_error: Invalid role")
        
        transaction.commit()
    except Exception as e:
        raise e
        

# == USER STUDENT =======================================================================
@app.get("/user/student/{id}")
async def get_student(id: str):
    if id == "all":
        return root.student
    else:
        id = int(id)
        return root.student[id] if id in root.student.keys() else {"error": "Student not found"}

# == USER INSTRUCTOR =====================================================================
@app.get("/user/instructor/{id}")
async def get_instructor(id: str):
    if id == "all":
        return root.instructor
    else:
        id = int(id)
        return root.instructor[id] if id in root.instructor.keys() else {"error": "Instructor not found"}

# == USER OTHERS ===========================================================================
@app.get("/user/other/{username}")
async def get_other(username: str):
    if username == "all":
        return root.otherUser
    else:
        return root.otherUser[username] if username in root.otherUser.keys() else {"error": "OtherUser not found"}

# == COURSE ===========================================================================
@app.get("/course/{course_id}")
async def get_course(course_id: str):
    if course_id == "all":
        return root.course
    else:
        return root.course[int(course_id)] if int(course_id) in root.course.keys() else {"error": "Course not found"}

@app.post("/course/new/", response_class=HTMLResponse)
async def post_course(request: Request, course_id: str = Form(...), course_name: str = Form(...), course_public: bool = Form(...), access_token: str = Cookie(None)):
    try:
        token = decodeJWT(access_token)
        instructor_id = token["id"]
        
        if int(course_id) in root.course.keys():
            raise HTTPException(404, detail="db_error: Course already exists")

        if not int(instructor_id) in root.instructor.keys():
            raise HTTPException(404, detail="db_error: Instructor not found")
        
        course_directory = videos_directory / course_id
        course_directory.mkdir(parents=True)
        
        root.course[int(course_id)] = Course(int(course_id), course_name, instructor_id, course_public)
        
        temp_instructor = Instructor(int(instructor_id), root.instructor[int(instructor_id)].first_name, root.instructor[int(instructor_id)].last_name, root.instructor[int(instructor_id)].email, root.instructor[int(instructor_id)].password)
        for c in root.instructor[int(instructor_id)].courses:
            temp_instructor.enrollCourse(c)
        temp_instructor.enrollCourse(int(course_id))
        root.instructor[int(instructor_id)] = temp_instructor
        
        transaction.commit()

        return RedirectResponse(url="/studyanytime", status_code=302, headers={"Set-Cookie": f"access_token={access_token}; Path=/"})
    except Exception as e:
        raise e
    
# == CHECK TOKEN =========================================================================
@app.get("/is_token_valid")
async def is_token_valid(request: Request):
    try:
        access_token = request.cookies.get("access_token")
        if decodeJWT(access_token) != None:
            return token_response(access_token)
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    except KeyError:
        raise HTTPException(status_code=401, detail="Token not found in cookies")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    